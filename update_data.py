import requests
from bs4 import BeautifulSoup
import json
import os
import re

def fetch_and_save():
    url = "https://www.pilio.idv.tw/ltobig/list.asp"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    # 1. 讀取現有資料
    if os.path.exists('data.json'):
        with open('data.json', 'r', encoding='utf-8') as f:
            try:
                final_data = json.load(f)
            except json.JSONDecodeError:
                final_data = []
    else:
        final_data = []

    existing_periods = {item['period'] for item in final_data}

    try:
        response = requests.get(url, headers=headers, timeout=15, verify=False)
        response.encoding = 'big5'
        soup = BeautifulSoup(response.text, 'html.parser')
        
        new_entries = []
        rows = soup.find_all('tr')
        
        for row in rows:
            tds = row.find_all('td')
            if len(tds) >= 2:
                col1 = tds[0].get_text(strip=True)
                col2 = tds[1].get_text(strip=True)
                
                if "," in col2:
                    # 提取期別 (MM/DD)
                    date_match = re.search(r'(\d{2}/\d{2})', col1)
                    display_date = date_match.group(1) if date_match else col1
                    
                    # 更安全的數字提取：直接用正則抓出所有連續數字
                    nums = re.findall(r'\d+', col2)
                    
                    # 補零處理 (例如 "5" 轉 "05")
                    nums = [n.padStart(2, '0') if len(n) == 1 else n for n in nums]
                    
                    # 大樂透必須要有 6 個一般號 + 1 個特別號 = 7 個號碼
                    if len(nums) == 7 and display_date not in existing_periods:
                        new_entries.append({
                            "period": display_date, 
                            "nums": nums[:6],
                            "s_num": nums[6]
                        })
        
        # 如果是新專案且完全沒抓到資料，拋出警告
        if not new_entries and not final_data:
            print("錯誤：未能從網頁解析出任何大樂透資料，請檢查網頁欄位結構。")
            return
        elif not new_entries:
            print("目前沒有新的大樂透開獎資料需要更新。")
            return

        # 3. 合併並排序 (由舊到新)
        combined_data = final_data + new_entries[::-1]
        
        # 4. 儲存為 JSON 檔案
        with open('data.json', 'w', encoding='utf-8') as f:
            json.dump(combined_data, f, ensure_ascii=False, indent=4)
            
        print(f"更新成功！新增了 {len(new_entries)} 期大樂透資料。")

    except Exception as e:
        print(f"更新失敗: {e}")

if __name__ == "__main__":
    fetch_and_save()
