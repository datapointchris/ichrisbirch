import { describe, it, expect } from 'vitest'
import { formatLogLine, formatLogJson, formatValue, levelName } from '../logger'
import { LogLevels } from 'consola'
import type { LogObject } from 'consola'

// Helper to build a LogObject matching consola's internal structure
function makeLogObj(overrides: Partial<LogObject> = {}): LogObject {
  return {
    level: LogLevels.info,
    type: 'info',
    tag: 'TestModule',
    args: ['test_event'],
    date: new Date(),
    ...overrides,
  } as LogObject
}

describe('formatValue', () => {
  it('returns strings as-is', () => {
    expect(formatValue('hello')).toBe('hello')
  })

  it('JSON-stringifies non-string values', () => {
    expect(formatValue(42)).toBe('42')
    expect(formatValue(true)).toBe('true')
    expect(formatValue(['a', 'b'])).toBe('["a","b"]')
    expect(formatValue({ key: 'val' })).toBe('{"key":"val"}')
  })
})

describe('levelName', () => {
  it('maps consola log levels to structlog-style names', () => {
    expect(levelName(LogLevels.error)).toBe('error')
    expect(levelName(LogLevels.warn)).toBe('warning')
    expect(levelName(LogLevels.info)).toBe('info')
    expect(levelName(LogLevels.debug)).toBe('debug')
    expect(levelName(LogLevels.verbose)).toBe('debug')
  })
})

describe('formatLogLine (structured reporter)', () => {
  it('includes timestamp, level, event, and module', () => {
    const { line } = formatLogLine(makeLogObj())

    expect(line).toMatch(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}/)
    expect(line).toContain('[info   ]')
    expect(line).toContain('test_event')
    expect(line).toContain('module=TestModule')
  })

  it('includes structured context as key=value pairs', () => {
    const logObj = makeLogObj({
      args: ['request_completed', { method: 'GET', status: 200, duration_ms: 42 }],
    })

    const { line } = formatLogLine(logObj)

    expect(line).toContain('request_completed')
    expect(line).toContain('method=GET')
    expect(line).toContain('status=200')
    expect(line).toContain('duration_ms=42')
  })

  it('maps levels correctly', () => {
    expect(formatLogLine(makeLogObj({ level: LogLevels.debug })).level).toBe('debug')
    expect(formatLogLine(makeLogObj({ level: LogLevels.info })).level).toBe('info')
    expect(formatLogLine(makeLogObj({ level: LogLevels.warn })).level).toBe('warning')
    expect(formatLogLine(makeLogObj({ level: LogLevels.error })).level).toBe('error')
  })

  it('JSON-stringifies complex context values', () => {
    const logObj = makeLogObj({
      args: ['test_event', { tags: ['a', 'b'] }],
    })

    const { line } = formatLogLine(logObj)
    expect(line).toContain('tags=["a","b"]')
  })

  it('omits null and undefined context values', () => {
    const logObj = makeLogObj({
      args: ['test_event', { present: 'yes', absent: undefined, empty: null }],
    })

    const { line } = formatLogLine(logObj)
    expect(line).toContain('present=yes')
    expect(line).not.toContain('absent')
    expect(line).not.toContain('empty')
  })

  it('works without context (event name only)', () => {
    const logObj = makeLogObj({ args: ['simple_event'] })

    const { line } = formatLogLine(logObj)
    expect(line).toContain('simple_event')
    expect(line).toContain('module=TestModule')
  })

  it('defaults to "app" when no tag is set', () => {
    const logObj = makeLogObj({ tag: '' })

    const { line } = formatLogLine(logObj)
    expect(line).toContain('module=app')
  })
})

describe('formatLogJson (JSON reporter for Loki)', () => {
  it('produces a flat JSON object with all fields', () => {
    const logObj = makeLogObj({
      args: ['request_completed', { method: 'POST', status: 201, duration_ms: 55 }],
    })

    const entry = formatLogJson(logObj)

    expect(entry.timestamp).toMatch(/^\d{4}-\d{2}-\d{2}T/)
    expect(entry.level).toBe('info')
    expect(entry.event).toBe('request_completed')
    expect(entry.module).toBe('TestModule')
    expect(entry.method).toBe('POST')
    expect(entry.status).toBe(201)
    expect(entry.duration_ms).toBe(55)
  })

  it('works without context', () => {
    const entry = formatLogJson(makeLogObj({ args: ['simple_event'] }))

    expect(entry.event).toBe('simple_event')
    expect(entry.module).toBe('TestModule')
    expect(Object.keys(entry)).toEqual(['timestamp', 'level', 'event', 'module'])
  })

  it('is valid JSON (serializable for Loki)', () => {
    const logObj = makeLogObj({
      args: ['test_event', { count: 5, tags: ['a'] }],
    })

    const entry = formatLogJson(logObj)
    const json = JSON.stringify(entry)
    const parsed = JSON.parse(json)

    expect(parsed.event).toBe('test_event')
    expect(parsed.count).toBe(5)
    expect(parsed.tags).toEqual(['a'])
  })
})
