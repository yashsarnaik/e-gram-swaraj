import requests
from bs4 import BeautifulSoup
import csv
import re

def clean_number(text):
    """Clean and convert text to number, handling Indian number format"""
    if not text or text.strip() == '':
        return 0
    # Remove commas and convert to float
    cleaned = re.sub(r'[,\s]', '', str(text))
    try:
        return float(cleaned)
    except:
        return 0

def create_alternative_csv_from_html():
    """Improved dynamic table extraction that ensures proper headers"""
    try:
        print("Trying alternative extraction method...")

        url = 'https://egramswaraj.gov.in/FileRedirect.jsp?FD=SchemeWiseExpenditureReport2025-2026/2813&name=2813.html'
        result = requests.get(url)
        soup = BeautifulSoup(result.text, 'html.parser')
        tables = soup.find_all('table')

        if not tables:
            print("No tables found.")
            return

        main_table = max(tables, key=lambda t: len(t.find_all('tr')))
        rows = main_table.find_all('tr')
        print(f"Found {len(rows)} rows in the main table")

        headers = []
        header_found = False
        data_start_index = 0

        # Step 1: Try to find a header row
        for idx, row in enumerate(rows):
            ths = row.find_all('th')
            tds = row.find_all('td')

            if ths:
                headers = [th.get_text(strip=True) for th in ths]
                header_found = True
                data_start_index = idx + 1
                print(f"Found header row using <th> at row {idx}")
                break
            elif not header_found and len(tds) >= 5:
                possible_header = [td.get_text(strip=True) for td in tds]
                # Heuristic: if all items are strings and no numbers
                if all(re.match(r'^[A-Za-z\s./\-()]+$', h) for h in possible_header):
                    headers = possible_header
                    header_found = True
                    data_start_index = idx + 1
                    print(f"Inferred header row using first <td> row at {idx}")
                    break

        if not headers:
            print("No valid header row found. Aborting.")
            return

        print(f"Extracted headers: {headers}")
        csv_data = [headers]

        # Step 2: Parse data rows after header
        for i in range(data_start_index, len(rows)):
            row = rows[i]
            cells = row.find_all(['td', 'th'])
            cell_texts = [cell.get_text(strip=True) for cell in cells]

            if not any(cell_texts):
                continue

            cleaned_row = []
            for j, text in enumerate(cell_texts):
                if j == 0:
                    cleaned_row.append(text.title())  # First column (State name)
                else:
                    cleaned_row.append(clean_number(text))

            # Adjust length
            while len(cleaned_row) < len(headers):
                cleaned_row.append("")
            if len(cleaned_row) > len(headers):
                cleaned_row = cleaned_row[:len(headers)]

            csv_data.append(cleaned_row)

        # Step 3: Write CSV
        with open('egramswaraj_data_alt.csv', 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows(csv_data)

        print(f"Saved to egramswaraj_data_alt.csv with {len(csv_data) - 1} data rows.")
        return csv_data

    except Exception as e:
        print(f"Error: {e}")
        return None



if __name__ == "__main__":
    
    # Run alternative method as well for comparison
    print("\n" + "="*50)
    create_alternative_csv_from_html()
    
    # Display some results
    try:
        import pandas as pd
        
        # Try to read and display the results
        try:
            df = pd.read_csv('egramswaraj_data.csv')
            print(f"\nMain extraction results:")
            print(f"Shape: {df.shape}")
            print(df.head())
        except:
            print("Could not read main CSV file")
            
        try:
            df_alt = pd.read_csv('egramswaraj_data_alt.csv')
            print(f"\nAlternative extraction results:")
            print(f"Shape: {df_alt.shape}")
            print(df_alt.head())
        except:
            print("Could not read alternative CSV file")
            
    except ImportError:
        print("\nInstall pandas to see data preview: pip install pandas")