def analyze(scores):

    if not scores:
        return "No data"

    avg=sum(scores)/len(scores)

    if avg<50:
        return "Weak understanding"
    if avg<75:
        return "Moderate understanding"

    return "Strong understanding"