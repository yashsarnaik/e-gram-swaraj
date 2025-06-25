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
    """Alternative method - parse HTML directly and extract table data more systematically"""
    try:
        print("Trying alternative extraction method...")
        
        result=requests.get('https://egramswaraj.gov.in/FileRedirect.jsp?FD=SummaryReport2025-2026&name=StateSummaryReport.html')
        
        content=result.text
        
        soup = BeautifulSoup(content, 'html.parser')
        
        # Find the main table with data
        tables = soup.find_all('table')
        
        if not tables:
            print("No tables found!")
            return
            
        # Usually the main data table is the largest one
        main_table = max(tables, key=lambda t: len(t.find_all('tr')))
        
        rows = main_table.find_all('tr')
        print(f"Found {len(rows)} rows in main table")
        
        # Create CSV data
        csv_data = []
        
        # Create headers based on table structure
        headers = ['State', 
                  'ZP_RV', 'ZP_PV', 'ZP_CV', 'ZP_JV', 'ZP_Receipts', 'ZP_Payments',
                  'BP_RV', 'BP_PV', 'BP_CV', 'BP_JV', 'BP_Receipts', 'BP_Payments', 
                  'VP_RV', 'VP_PV', 'VP_CV', 'VP_JV', 'VP_Receipts', 'VP_Payments']
        
        csv_data.append(headers)
        
        # Process each row
        for i, row in enumerate(rows):
            cells = row.find_all(['td', 'th'])
            
            if len(cells) < 2:
                continue
                
            # Get all cell text
            cell_texts = [cell.get_text(strip=True) for cell in cells]
            
            # Skip completely empty rows
            if all(not text for text in cell_texts):
                continue
                
            first_cell = cell_texts[0].upper()
            
            # Print row info for debugging
            print(f"Row {i}: First cell = '{first_cell}', Total cells = {len(cells)}")
            
            # Check if this looks like a data row
            if (first_cell and 
                not first_cell.startswith('STATE') and 
                not 'PANCHAYAT' in first_cell and
                not first_cell in ['RV', 'PV', 'CV', 'JV'] and
                len(cell_texts) > 5):  # Should have multiple data columns
                
                # Clean the row data
                clean_row = [cell_texts[0].title()]  # State name
                
                # Process remaining cells as numbers
                for j in range(1, len(cell_texts)):
                    clean_row.append(clean_number(cell_texts[j]))
                
                # Pad or truncate to match header length
                while len(clean_row) < len(headers):
                    clean_row.append(0)
                    
                if len(clean_row) > len(headers):
                    clean_row = clean_row[:len(headers)]
                
                csv_data.append(clean_row)
                print(f"Added data row: {clean_row[0]} with {len(clean_row)} columns")
        
        # Save alternative CSV
        with open('egramswaraj_data_alt.csv', 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerows(csv_data)
        
        print(f"\nAlternative extraction completed!")
        print(f"Saved to: egramswaraj_data_alt.csv")
        print(f"Total data rows: {len(csv_data) - 1}")  # Subtract header row
        
        return csv_data
        
    except Exception as e:
        print(f"Error in alternative extraction: {e}")
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