def route_query(question: str):

    q = question.lower()

    if any(x in q for x in ["author", "title", "year"]):
        return "metadata"

    if "abstract" in q:
        return "abstract"

    if any(x in q for x in ["method", "model", "architecture"]):
        return "methodology"

    if any(x in q for x in ["result", "accuracy", "performance"]):
        return "results"

    if "reference" in q:
        return "references"

    return "general"