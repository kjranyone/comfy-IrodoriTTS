AUTHOR = "kjranyone"


def node_id(*parts: str) -> str:
    return ".".join([AUTHOR, *parts])


def node_category(*parts: str) -> str:
    return "/".join([AUTHOR, *parts])
