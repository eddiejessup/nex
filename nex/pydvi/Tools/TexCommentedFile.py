def without_comments(f):
    while True:
        line = f.readline()
        if not line:
            return
        comment_start_index = line.find('%')
        if comment_start_index != -1:
            line = line[:comment_start_index]
        line = line.strip()
        if line:
            yield line
