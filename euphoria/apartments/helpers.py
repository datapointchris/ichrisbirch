def convert_data_types_from_strings(info, mapping):
    converted = {}
    for k, v in info.items():
        if v == '' or v is None or v == 'None':
            converted[k] = None
        else:
            data_type = mapping.get(k)
            match data_type:
                case 'integer':
                    converted[k] = int(v)
                case 'text':
                    converted[k] = v.strip()
                case 'boolean':
                    converted[k] = int(v)

    return converted
