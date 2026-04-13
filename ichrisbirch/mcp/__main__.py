import os
from typing import Literal
from typing import cast

from ichrisbirch.mcp.server import mcp

Transport = Literal['stdio', 'sse', 'streamable-http']
transport = cast(Transport, os.environ.get('MCP_TRANSPORT', 'stdio'))
mcp.run(transport=transport)
