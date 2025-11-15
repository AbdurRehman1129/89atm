import csv
import re
import sys
import argparse

#!/usr/bin/env python3
# arrange.py - list IMEIs with offer amount 452 from a CSV (default: results.csv)


def is_452(value):
    if value is None:
        return False
    digits = re.sub(r'\D', '', value)
    return digits == '452'

def main():
    parser = argparse.ArgumentParser(description='Find IMEIs with offer amount 452 in a CSV.')
    parser.add_argument('csvfile', nargs='?', default='results.csv', help='CSV file (default: results.csv)')
    parser.add_argument('-o', '--output', help='Write matching IMEIs to FILE instead of stdout')
    args = parser.parse_args()

    try:
        with open(args.csvfile, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            matches = [row.get('imei', '').strip() for row in reader if is_452(row.get('offer_amount'))]
    except FileNotFoundError:
        print(f'File not found: {args.csvfile}', file=sys.stderr)
        sys.exit(1)

    if not matches:
        print('No IMEIs found with amount 452')
        return

    if args.output:
        with open(args.output, 'w', encoding='utf-8') as out:
            out.write('\n'.join(matches))
        print(f'Wrote {len(matches)} IMEI(s) to {args.output}')
    else:
        for imei in matches:
            print(imei)

if __name__ == '__main__':
    main()