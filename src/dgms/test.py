def format_name_string(name):
    if len(name)>17:
        name= name[:16]+"\n"+name[16:]
    return name

name="AWSServiceCatalogEndUserAccess"

name=format_name_string(name)

print(name)