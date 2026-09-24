#!/usr/bin/env python3
"""
WISCONSIN DATA PROCESSOR
Direct processor for WI_HeirFinder_Priority_Targets CSV
Outputs ready-to-use Google Sheets format + Contact Finder batch

Usage:
    python process_wisconsin_data.py WI_HeirFinder_Priority_Targets.csv
"""

import csv
import sys
import json
from datetime import datetime
from collections import defaultdict


class WisconsinDataProcessor:
    def __init__(self):
        self.current_year = datetime.now().year
        self.min_amount = 100

    def clean_amount(self, amount_str):
        try:
            return float(str(amount_str).replace('$', '').replace(',', '').strip())
        except (ValueError, AttributeError):
            return 0.0

    def calculate_priority(self, amount, report_year):
        try:
            age = self.current_year - int(report_year)
        except (ValueError, TypeError):
            age = 99
        score = 0
        if amount >= 1000: score += 3
        elif amount >= 500: score += 2
        elif amount >= 250: score += 1
        if age <= 3: score += 3
        elif age <= 5: score += 2
        elif age <= 10: score += 1
        score += 3  # address completeness (passed validation)
        if score >= 8: return 'HIGH', score
        if score >= 5: return 'MEDIUM', score
        return 'LOW', score

    def clean_name(self, last_name, first_name, mi=''):
        last_name = (last_name or '').strip()
        first_name = (first_name or '').strip()
        if 'ESTATE OF' in last_name.upper() or 'TRUST' in last_name.upper():
            return last_name, '', ''
        if not first_name:
            return last_name.title(), '', ''
        return last_name.title(), first_name.title(), (mi or '').strip().upper()

    def clean_address(self, address1, address2=''):
        addr = (address1 or '').strip().title()
        if address2 and address2.strip():
            addr += ', ' + address2.strip().title()
        return addr

    def is_valid_record(self, row):
        last = (row.get('LastName', '') or '')
        is_entity = 'ESTATE OF' in last.upper() or 'TRUST' in last.upper()
        if not row.get('LastName') and not row.get('FirstName'):
            return False, "No name"
        # Estates/trusts often lack a street address but are still claimable
        if not is_entity and not row.get('Address 1') and not row.get('City'):
            return False, "No address"
        if self.clean_amount(row.get('Amount', '0')) < self.min_amount:
            return False, "Below minimum amount"
        if not row.get('Year'):
            return False, "No year"
        return True, "Valid"

    def process_csv(self, input_file):
        print(f"Processing {input_file}...")
        records_in = 0
        skipped = defaultdict(int)
        output_records = []

        with open(input_file, 'r', encoding='utf-8', errors='replace') as f:
            reader = csv.DictReader(f)
            for row in reader:
                records_in += 1
                valid, reason = self.is_valid_record(row)
                if not valid:
                    skipped[reason] += 1
                    continue

                last, first, middle = self.clean_name(
                    row.get('LastName', ''), row.get('FirstName', ''), row.get('MI', ''))
                if middle:
                    # Single letter = initial (add period); longer = full middle name
                    mi_fmt = f"{middle}." if len(middle) == 1 else middle
                    full_name = f"{first} {mi_fmt} {last}"
                elif first:
                    full_name = f"{first} {last}"
                else:
                    full_name = last

                address = self.clean_address(row.get('Address 1', ''), row.get('Addres 2', ''))
                city = (row.get('City', '') or '').strip().title()
                state = (row.get('State', 'WI') or 'WI').strip().upper()
                zip_code = (row.get('Zip', '') or '').strip()
                amount = self.clean_amount(row.get('Amount', '0'))
                property_type = (row.get('Property Type', '') or '').strip()
                try:
                    report_year = int(row.get('Year', self.current_year))
                except (ValueError, TypeError):
                    report_year = self.current_year
                property_id = (row.get('Property ID', '') or '').strip()

                priority, score = self.calculate_priority(amount, report_year)
                record_id = f"{report_year}-{property_id}"
                complete = 'YES' if (address and city and state) else 'NO'

                output_records.append({
                    'Record_ID': record_id, 'Full_Name': full_name,
                    'First_Name': first, 'Last_Name': last, 'Address': address,
                    'City': city, 'State': state, 'ZIP': zip_code,
                    'Amount': f"{amount:.2f}", 'Property_Type': property_type,
                    'Report_Year': report_year, 'Data_Source': 'Wisconsin',
                    'Priority': priority, 'Age_Years': self.current_year - report_year,
                    'Complete_Record': complete, 'Score': score,
                })

        priority_order = {'HIGH': 3, 'MEDIUM': 2, 'LOW': 1}
        output_records.sort(
            key=lambda x: (priority_order.get(x['Priority'], 0), float(x['Amount'])),
            reverse=True)

        self._print_report(records_in, output_records, skipped)
        return output_records

    def _print_report(self, records_in, output_records, skipped):
        print("\n" + "=" * 60)
        print("PROCESSING SUMMARY")
        print("=" * 60)
        print(f"Total records read:    {records_in:,}")
        print(f"Valid records output:  {len(output_records):,}")
        print(f"Records skipped:       {records_in - len(output_records):,}")
        if skipped:
            print("\nSkipped breakdown:")
            for reason, count in sorted(skipped.items(), key=lambda x: -x[1]):
                print(f"  {reason}: {count:,}")
        pc, pv = defaultdict(int), defaultdict(float)
        for r in output_records:
            pc[r['Priority']] += 1
            pv[r['Priority']] += float(r['Amount'])
        print("\nPriority distribution:")
        for p in ['HIGH', 'MEDIUM', 'LOW']:
            print(f"  {p}: {pc[p]:,} records (${pv[p]:,.2f})")
        total = sum(float(r['Amount']) for r in output_records)
        print(f"\nTotal opportunity: ${total:,.2f}")
        if output_records:
            print(f"Average amount:    ${total/len(output_records):,.2f}")
            print("\nTop 10 opportunities:")
            for i, r in enumerate(output_records[:10], 1):
                print(f"  {i:2}. {r['Full_Name']}: ${float(r['Amount']):,.2f} ({r['City']})")

    def write_csv(self, records, output_file):
        fieldnames = ['Record_ID', 'Full_Name', 'First_Name', 'Last_Name',
                      'Address', 'City', 'State', 'ZIP', 'Amount', 'Property_Type',
                      'Report_Year', 'Data_Source', 'Priority', 'Age_Years',
                      'Complete_Record', 'Score']
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(records)
        print(f"\n[OK] CSV written to: {output_file}")

    def write_json(self, records, output_file):
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(records, f, indent=2)
        print(f"[OK] JSON written to: {output_file}")

    def generate_contact_batch(self, records, batch_size=50):
        high = [r for r in records if r['Priority'] == 'HIGH'][:batch_size]
        batch = [{
            'record_id': r['Record_ID'], 'full_name': r['Full_Name'],
            'old_address': f"{r['Address']}, {r['City']}, {r['State']} {r['ZIP']}",
            'amount': r['Amount'], 'property_type': r['Property_Type'],
        } for r in high]
        with open('contact_finder_batch.json', 'w', encoding='utf-8') as f:
            json.dump(batch, f, indent=2)
        print(f"[OK] Contact batch ({len(batch)}) -> contact_finder_batch.json")


def main():
    if len(sys.argv) < 2:
        print("Usage: python process_wisconsin_data.py <input_csv>")
        sys.exit(1)
    input_file = sys.argv[1]
    base = input_file.rsplit('.', 1)[0]
    p = WisconsinDataProcessor()
    records = p.process_csv(input_file)
    if not records:
        print("\n[ERROR] No valid records found.")
        sys.exit(1)
    p.write_csv(records, f"{base}_CLEANED.csv")
    p.write_json(records, f"{base}_CLEANED.json")
    p.generate_contact_batch(records, batch_size=50)
    print("\n" + "=" * 60)
    print("READY TO IMPORT")
    print("=" * 60)
    print(f"1. Google Sheets -> File -> Import -> {base}_CLEANED.csv")
    print("2. Import to 'Clean Data' tab")
    print("3. Feed contact_finder_batch.json to Contact Finder GPT")


if __name__ == '__main__':
    main()
