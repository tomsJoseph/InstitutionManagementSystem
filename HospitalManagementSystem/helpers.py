def serialize_qs(qs, fields):
    rv = []
    for obj in qs:
        obj_dict = []
        for field in fields:
            obj_dict.append(getattr(obj, field))
        rv.append(obj_dict)
    return rv


