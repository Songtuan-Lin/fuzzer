def getAllTuples(all_combs):
    if len(all_combs) == 0:
        return [tuple()]
    results = set()
    tail = all_combs.pop(-1)
    heads = getAllTuples(all_combs)
    for e in tail:
        for t in heads:
            t= list(t)
            t.append(e)
            results.add(tuple(t))
    return results