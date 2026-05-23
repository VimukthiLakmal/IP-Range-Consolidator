from ip_utils import ip_to_int, int_to_ip

def should_merge(prev_end, curr_start, strict_merge=False):
    if curr_start <= prev_end + 1:
        return True
    return False


def octet_block(ip_int):
    return str(int_to_ip(ip_int)).split('.')[2]


def merge_ranges(df, strict_merge=False):
    intervals = []

    # Step 1: convert to numeric intervals
    for _, row in df.iterrows():
        start = ip_to_int(row['First IP'])
        end = ip_to_int(row['Last IP'])

        if start is None or end is None:
            continue

        if start > end:
            start, end = end, start

        intervals.append((start, end))

    # Step 2: sort
    intervals.sort(key=lambda x: x[0])

    if not intervals:
        return []

    # Step 3: merge
    merged = [intervals[0]]

    for curr_start, curr_end in intervals[1:]:
        prev_start, prev_end = merged[-1]

        can_merge = should_merge(prev_end, curr_start, strict_merge)

        # OCTET RULE
        if can_merge and not strict_merge:
            prev_octet = octet_block(prev_end)
            curr_octet = octet_block(curr_start)

            if prev_octet != curr_octet:
                can_merge = False

        if can_merge:
            merged[-1] = (prev_start, max(prev_end, curr_end))
        else:
            merged.append((curr_start, curr_end))

    return merged