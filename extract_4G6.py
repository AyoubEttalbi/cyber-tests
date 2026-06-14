import json, urllib.request, sys

TOKEN = open('/tmp/cur_token.txt').read().strip()
H = 'Origin: https://student.emsi.ma'

all_records = []
all_elements = [53660, 53661, 53662, 53663, 53664, 53665, 53666, 53667, 53668, 53669, 53670, 53671, 53672]

for eeid in all_elements:
    try:
        req = urllib.request.Request(
            'https://sis-api.emsi.ma/v1/neo-instructor/grades/page',
            data=json.dumps({"where": {"evaluationElementID": eeid}, "page": 1, "pageSize": 50}).encode(),
            headers={
                'Authorization': f'Bearer {TOKEN}',
                'Content-Type': 'application/json',
                'Origin': 'https://student.emsi.ma'
            },
            method='POST'
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            records = data.get('data', [])
            for r in records:
                all_records.append(r)
            non_null = sum(1 for g in records if g.get('grade') is not None)
            print(f'EvalEl {eeid}: {len(records)} records, {non_null} non-null')
    except Exception as ex:
        print(f'EvalEl {eeid}: error {ex}')

out_path = '/home/Student/projects/cyper/attacks/4IIRM_G6_grades.json'
with open(out_path, 'w') as f:
    json.dump(all_records, f, indent=2, default=str)

print(f'\nTotal: {len(all_records)} records saved to {out_path}')

eids = set()
for r in all_records:
    eids.add(r.get("enrollmentID", 0))
print(f'Unique enrollmentIDs: {len(eids)}')
nn = sum(1 for r in all_records if r.get("grade") is not None)
print(f'Non-null grades: {nn}')
