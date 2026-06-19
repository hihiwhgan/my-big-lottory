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
            # 尋找具備特定 class 的網頁欄位
            td_date = row.find('td', class_='date-cell')
            td_nums = row.find('td', class_='number-cell')
            td_bonus = row.find('td', class_='bonus-cell')
            
            # 確保三個核心欄位同時存在
            if td_date and td_nums and td_bonus:
                raw_date = td_date.get_text(strip=True)
                raw_nums = td_nums.get_text(strip=True)
                raw_bonus = td_bonus.get_text(strip=True)
                
                # 1. 提取期別 (抓取第一個出現的 MM/DD 格式)
                date_match = re.search(r'(\d{2}/\d{2})', raw_date)
                display_date = date_match.group(1) if date_match else raw_date
                
                if display_date in existing_periods:
                    continue
                
                # 2. 解析一般號 (用正則抓出所有數字)
                nums = re.findall(r'\d+', raw_nums)
                nums = [n.zfill(2) for n in nums]  # 補零處理
                
                # 3. 解析特別號
                bonus_match = re.search(r'\d+', raw_bonus)
                special_num = bonus_match.group(0).zfill(2) if bonus_match else None
                
                # 驗證：大樂透必須要有 6 個一般號與 1 個特別號
                if len(nums) == 6 and special_num:
                    new_entries.append({
                        "period": display_date, 
                        "nums": nums,
                        "s_num": special_num
                    })
        
        if not new_entries and not final_data:
            print("錯誤：未能從網頁解析出任何大樂透資料。請檢查 Class 名稱是否正確。")
            return
        elif not new_entries:
            print("目前沒有新的大樂透開獎資料需要更新。")
            return

        # 合併並排序 (由舊到新)
        combined_data = final_data + new_entries[::-1]
        
        with open('data.json', 'w', encoding='utf-8') as f:
            json.dump(combined_data, f, ensure_ascii=False, indent=4)
            
        print(f"更新成功！新增了 {len(new_entries)} 期大樂透資料。")

    except Exception as e:
        print(f"更新失敗: {e}")

if __name__ == "__main__":
    fetch_and_save()
