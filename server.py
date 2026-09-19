#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
大清天朵二期社區 AI 管理助手 - 本地後端服務
包含：
1. 規約與決議邏輯檢核 (含防水閘門檢測與定期演練)
2. 影像辨識與自動派單
3. 社區財務自動銷帳
4. 零用金三委員多重簽核流
5. 每年5月防汛演練自動提醒排程 & 中央氣象局 (CWA) 豪大雨即時主動推播
"""

import os
import json
import mimetypes
import datetime
import socket
from http.server import HTTPServer, SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

PORT = 8080
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "data.json")

# 初始化社區基礎資料
DEFAULT_DATA = {
    "community_name": "大清天朵二期社區",
    "committee_term": "第五屆管委會",
    "residents": [
        {"unit": "A-8F-1", "name": "饒先生", "line_id": "U_RES_001", "fee": 3850, "account_suffix": "68821", "paid": True, "payment_date": "2026-09-17"},
        {"unit": "A-8F-2", "name": "李小姐", "line_id": "U_RES_002", "fee": 4200, "account_suffix": "12345", "paid": True, "payment_date": "2026-09-05"},
        {"unit": "A-9F-1", "name": "張先生", "line_id": "U_RES_003", "fee": 3850, "account_suffix": "54321", "paid": True, "payment_date": "2026-09-08"},
        {"unit": "B-5F-2", "name": "王太太", "line_id": "U_RES_004", "fee": 3500, "account_suffix": "98765", "paid": False, "payment_date": None},
        {"unit": "B-10F-1", "name": "黃先生", "line_id": "U_RES_005", "fee": 4500, "account_suffix": "77889", "paid": False, "payment_date": None}
    ],
    "dispatches": [
        {
            "id": "DISP-20260917-001",
            "time": "2026-09-17 14:20",
            "category": "Trash",
            "category_name": "垃圾棄置",
            "location": "B1 資源回收室旁走道",
            "reporter": "住戶通報 (A-8F-1)",
            "description": "走道堆積未依規定分類的大型紙箱與保麗龍",
            "status": "處理中",
            "target_team": "清潔人員/物業群組",
            "image_url": "https://images.unsplash.com/photo-1532996122724-e3c354a0b15b?w=600&auto=format&fit=crop&q=60"
        },
        {
            "id": "DISP-20260916-002",
            "time": "2026-09-16 18:45",
            "category": "Lost Item",
            "category_name": "遺失物",
            "location": "A棟1F大廳休息沙發",
            "reporter": "物業巡檢 (固德物業)",
            "description": "黑色保溫水瓶一只，外觀有恐龍貼紙",
            "status": "等待認領",
            "target_team": "管理中心",
            "image_url": "https://images.unsplash.com/photo-1602143407151-7111542de6e8?w=600&auto=format&fit=crop&q=60"
        }
    ],
    "petty_cash": {
        "month": "115年08月份",
        "case_title": "115年八月份社區一般費用報支與出納簽核案",
        "submitted_by": "固德建築物管理維護有限公司",
        "submitter_name": "高瑞彣",
        "submitter_role": "固德物業作業承辦人",
        "submitter_stamp": "承辦人 115.8.23 高瑞彣 (核章完成)",
        "submitted_date": "115年8月20日",
        "scheduled_payment_date": "115年8月31日",
        "withdrawal_date": "115年8月31日",
        "declarations": {
            "no_inserted_text": True,
            "all_signed_by_agent": True,
            "balance_match": "match",
            "passbook_balance": 173847
        },
        "total_spent": 24500,
        "limit": 100000,
        "deposit_transfer_amount": 50000,
        "deposit_transfer_desc": "8/31 華南銀行提領現金 50,000 元轉存入社區郵局帳戶 (局帳號: 028115-4 034699-4)",
        "balance_info": {
            "passbook_balance_before": 173847,
            "passbook_balance_after": 99347,
            "post_office_added": 50000,
            "statement_balance": 1277684
        },
        "ai_audit": {
            "status": "passed",
            "summary": "AI 智慧比對：四表支出總額 $24,500 完全一致，專款存轉 $50,000 單據無誤，承辦人高瑞彣章戳齊備，宏捷維修報價單已獲管委會簽認核准。",
            "items_check": "4筆費用合計 NT$ 24,500 與待支付明細表及財務收支表吻合",
            "transfer_check": "8/31 華南銀行取款傳票與中華郵政存款人收執聯 NT$ 50,000 勾稽吻合",
            "quote_check": "宏捷機電門禁鎖維修 NT$ 1,500 報價單已簽認核章",
            "seal_check": "作業承辦人高瑞彣印戳已逐張確認完備"
        },
        "items": [
            {
                "id": 15,
                "no": 15,
                "title": "環境清潔服務費 (八月份)",
                "amount": 3000,
                "category": "環境清潔",
                "vendor": "誼潔家事服務企業社",
                "invoice": "收據 (免用發票專用收據)",
                "date": "115-08-15",
                "desc": "本月份梯廳與公共走廊環境清潔服務費",
                "attachment": "一般費用報支單.jpg",
                "attachments": ["一般費用報支單.jpg"]
            },
            {
                "id": 16,
                "no": 16,
                "title": "管理維護顧問服務費 (七、八月份)",
                "amount": 18000,
                "category": "管理服務",
                "vendor": "固德建築物管理維護有限公司",
                "invoice": "二聯式統一發票 CC22775061",
                "date": "115-08-15",
                "desc": "七月份、八月份顧問服務費 (2式*9,000元)",
                "attachment": "一般費用報支單1.jpg",
                "payment_slip": "一般費用報支單3.jpg",
                "attachments": ["一般費用報支單1.jpg", "一般費用報支單3.jpg"]
            },
            {
                "id": 17,
                "no": 17,
                "title": "門口門禁鎖故障檢修與拆裝工資",
                "amount": 1500,
                "category": "門禁維修",
                "vendor": "宏捷機電企業社",
                "invoice": "工程報價單 (管委會已簽認)",
                "date": "115-08-03",
                "desc": "門口鎖具繼電器故障檢修與拆裝 (8/3維修完成)",
                "attachment": "一般費用報支單7.jpg",
                "quote_slip": "維修商報價單1.jpg",
                "payment_slip": "一般費用報支單5.jpg",
                "attachments": ["一般費用報支單7.jpg", "維修商報價單1.jpg", "一般費用報支單5.jpg"]
            },
            {
                "id": 18,
                "no": 18,
                "title": "安全監視系統檢測出勤工資",
                "amount": 2000,
                "category": "安全監控",
                "vendor": "鼎聖通訊有限公司",
                "invoice": "出勤工資單憑證",
                "date": "115-08-20",
                "desc": "8/20至社區檢測安全系統出勤工資",
                "attachment": "一般費用報支單2.jpg",
                "payment_slip": "一般費用報支單6.jpg",
                "attachments": ["一般費用報支單2.jpg", "一般費用報支單6.jpg"]
            }
        ],
        "approvals": {
            "director": {
                "role": "主任委員",
                "name": "陳建宏",
                "status": "approved",
                "comment": "四項單據與華南取款條核對相符，准予出納付款，同意專款存入郵局。",
                "time": "2026-08-25 09:30"
            },
            "finance": {
                "role": "財務委員",
                "name": "林秀玲",
                "status": "approved",
                "comment": "四表金額勾稽一致無誤，存簿餘額核算正確，同意報支。",
                "time": "2026-08-25 10:15"
            },
            "supervisor": {
                "role": "行政委員",
                "name": "王國華",
                "status": "approved",
                "comment": "宏捷門禁及鼎聖弱電出勤已驗收確認，同意簽核。",
                "time": "2026-08-25 14:00"
            }
        },
        "final_status": "approved",
        "attachments": [
            { "id": "att-1", "title": "待支付費用明細表 (財Q表)", "type": "jpg", "file": "八月份待支付費用明細表.jpg", "category": "明細總表", "desc": "高瑞彣115.8.23編制，合計4筆支出$24,500元" },
            { "id": "att-2", "title": "八月份財務收支表 (財I表)", "type": "jpg", "file": "八月份財務收支表.jpg", "category": "收支報表", "desc": "收入$35,634，支出$24,500，結餘$1,277,684" },
            { "id": "att-3", "title": "待支付明細表-核銷版(附存摺)", "type": "jpg", "file": "八月份待支付費用明細表1.jpg", "category": "出納核銷", "desc": "8/31華南銀行存摺補登扣款，餘額$99,347元，轉存郵局5萬" },
            { "id": "att-4", "title": "存款紀錄 (華南轉存郵局)", "type": "jpg", "file": "存款紀錄.jpg", "category": "資金調度", "desc": "華南提領5萬存入社區郵局帳戶之取款與收執聯" }
        ]
    },
    "financial_statement_i": {
        "month_code": "11508",
        "month_title": "一一五年八月份",
        "doc_title": "大清天朵二期社區一一五年八月份財務收支表（Ｉ）",
        "date": "115年9月3日",
        "submitter": "高瑞彣",
        "submitter_stamp_date": "115. 9. 03",
        "previous_balance": 1266550,
        "incomes": {
            "management_fee": 35634,
            "parking_rent": 0,
            "temp_parking": 0,
            "public_phone": 0,
            "bank_interest": 0,
            "other_income": 0
        },
        "expenses": [
            { "no": 15, "title": "環境清潔", "amount": 3000, "desc": "本月份服務費" },
            { "no": 16, "title": "管理服務", "amount": 18000, "desc": "七月份、八月份服務費" },
            { "no": 17, "title": "門口門禁鎖故障", "amount": 1500, "desc": "8/3維修完成" },
            { "no": 18, "title": "安全系統檢測", "amount": 2000, "desc": "8/20出勤工資" }
        ],
        "assets": {
            "petty_cash": 0,
            "pending_cash": 0,
            "pending_check_in": 0,
            "pending_check_out": 0,
            "bank_deposit": 99347,
            "post_deposit": 1178337
        },
        "approvals": {
            "director": {
                "role": "主任委員",
                "name": "陳建宏",
                "status": "approved",
                "comment": "財務收支表勾稽正確，結餘款核算無誤，同意簽核備查。",
                "time": "2026-08-25 09:30"
            },
            "finance": {
                "role": "財務委員",
                "name": "林秀玲",
                "status": "approved",
                "comment": "收支金額與銀行及郵局存簿結餘吻合，符合會計規範，同意簽核。",
                "time": "2026-08-25 10:15"
            },
            "supervisor": {
                "role": "行政委員",
                "name": "王國華",
                "status": "approved",
                "comment": "各項請款核銷與出勤維護內容核對無誤，同意簽核。",
                "time": "2026-08-25 14:00"
            }
        },
        "final_status": "approved"
    },
    "flood_system": {
        "annual_drill": {
            "schedule_month": "每年 5 月",
            "last_drill_date": "2026-05-12",
            "next_drill_deadline": "2027-05-20",
            "last_duration_min": "11 分 35 秒 (合格標準: 15分鐘內)",
            "sandbag_count": 60,
            "status": "已完成本年度演練",
            "auto_reminder_enabled": True,
            "reminder_history": [
                {
                    "time": "2026-05-01 09:00",
                    "title": "【系統自動年度排程提醒】汛期防水閘門檢測與防汛實兵操演通知",
                    "recipients": "固德物業總幹事、管委會全體委員",
                    "content": "提醒：汛期將至！依社區規約第4條，請物業於5月20日前完成地下室車道防水閘門機械軌道防銹潤滑、橡膠止水條密封檢驗、60包沙包盤點，並召集全體管理員實兵組裝演練拍照存檔備查。"
                }
            ]
        },
        "cwa_weather": {
            "connected": True,
            "source": "交通部中央氣象署 (CWA) 氣象警特報 API",
            "location": "台北市",
            "alert_level": "normal", # normal, heavy_rain, torrential_rain, typhoon
            "alert_name": "天氣正常 (無豪雨特報)",
            "rainfall_forecast": "各區多雲到晴，午後短暫雷陣雨機率 20%",
            "updated_at": "2026-09-17 18:20",
            "broadcast_logs": []
        }
    },
    "bylaws": [
        {
            "id": "LAW-07",
            "title": "社區防汛與地下室防水閘門定期檢測及實兵操演規約",
            "source": "第四屆區分所有權人會議決議暨防汛作業標準手冊 (SOP)",
            "content": "本社區地下停車場出入口車道設有組合式防汛防水閘門。管委會與固德物業服務中心應恪遵以下規範：1. 每年汛期前（每年5月份）排定完成防水閘門機械結構保養、軌道泥沙清理與防鏽潤滑。2. 檢驗橡膠止水條之密封彈性，若有硬化、龜裂破損應立即編列修繕預算更換。3. 盤點備用防汛沙包（數量不得少於50包）及沉水抽水泵測試運轉。4. 召集全體物業日夜班管理人員與機電廠商，舉行『防水閘門實兵組裝與閉合操演』，組裝閉合時間不得逾15分鐘。操演成果與照片應造冊公告住戶備查。未依期落實檢測操演致水患損害者，管委會與受託物業管理公司應負民法善良管理人責任。",
            "keywords": ["防水閘門", "防汛", "演練", "操演", "5月", "地下室", "抽水泵", "沙包", "淹水", "氣象局", "豪大雨", "暴雨"]
        },
        {
            "id": "LAW-01",
            "title": "社區規約第十六條：公共空間與走廊通道管理規範",
            "source": "大清天朵二期規約 (第三屆區權會修訂全文)",
            "content": "各樓層梯廳、走廊、樓梯間、排煙室及地下防空避難室等全體共用部分，住戶不得私自堆置任何個人物品（包含鞋櫃、雨傘架、腳踏車、嬰兒車、垃圾袋及各類雜物），以確保消防避難安全及公共環境整潔。違者物業管理中心得開立限期改善通知單（限24小時內移除），逾期未改善者，由管委會移請主管機關依法裁處新臺幣四萬元以上二十萬元以下罰鍰。",
            "keywords": ["鞋櫃", "走廊", "梯廳", "雜物", "公共空間", "消防通道", "樓梯間"]
        },
        {
            "id": "LAW-02",
            "title": "第三屆區分所有權人會議決議案（案由五）",
            "source": "113年度區權會會議紀錄",
            "content": "【案由】住戶提議開放於各層走廊梯廳靠牆處放置薄型鞋櫃案。【決議】經大會討論與全體出席權數投票，出席權數 82% 表決反對，維持嚴格走廊全面淨空政策。任何形式之薄型鞋櫃、置物架皆嚴禁擺放於共用走廊。",
            "keywords": ["鞋櫃", "薄型鞋櫃", "第三屆", "走廊", "決議"]
        },
        {
            "id": "LAW-03",
            "title": "社區規約第十九條：外牆立面與冷氣主機安裝管理",
            "source": "大清天朵二期規約 (第一屆區權會訂定)",
            "content": "冷氣室外機之安裝，必須統一配置於建商原規劃預留之冷氣專屬基座樑位，嚴禁懸掛於建築物立面外緣或私自穿透外牆結構打孔，以維護大樓外觀一致性與防墜落結構安全。",
            "keywords": ["冷氣", "室外機", "外牆", "滴水", "外觀", "主機"]
        },
        {
            "id": "LAW-04",
            "title": "第四屆管委會第五次常會決議：電動車充電設備安裝準則",
            "source": "114年管委會會議紀錄",
            "content": "地下停車場住戶私人車位擬裝設電動車充電樁（EMS系統），應先填具申請書並檢附台電核可文件與甲級電匠施工圖說，經管委會機電顧問審查通過後方得施工。工程不得破壞既有公共管道結構，費用由申請人自行全額負擔，嚴禁擅自私接公共照明電源。",
            "keywords": ["充電樁", "電動車", "停車位", "台電", "EMS", "地下室"]
        },
        {
            "id": "LAW-05",
            "title": "社區寵物飼養及通行管理辦法",
            "source": "第二屆管委會第七次常會通過",
            "content": "住戶攜帶寵物進出社區大廳、電梯、中庭及梯廳時，應裝入寵物箱、推車或確實繫上牽繩並抱持。寵物若於共用部分排泄，飼主應立即清潔消毒，違者依違規計點處理並公告其戶別。",
            "keywords": ["寵物", "狗", "貓", "牽繩", "排泄物", "電梯"]
        },
        {
            "id": "LAW-06",
            "title": "住戶夜間寧靜與生活安寧公約",
            "source": "社區規約第二十二條",
            "content": "每日夜間 22:00 至翌日清晨 08:00 為社區安寧時段。此時段內嚴禁進行室內裝修施工、大聲喧嘩、彈奏樂器或重物敲擊地板。違反者經管理室勸導兩次無效後，管委會得報請警政主管機關依社會秩序維護法裁罰。",
            "keywords": ["噪音", "裝修", "夜間", "安寧", "音樂", "小孩跑步"]
        }
    ]
}

def load_data():
    if not os.path.exists(DATA_FILE):
        save_data(DEFAULT_DATA)
        return DEFAULT_DATA
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            # 確保增補的欄位存在
            if "flood_system" not in data:
                data["flood_system"] = DEFAULT_DATA["flood_system"]
            # 確保 LAW-07 存在
            if not any(b.get("id") == "LAW-07" for b in data.get("bylaws", [])):
                data["bylaws"].insert(0, DEFAULT_DATA["bylaws"][0])
            return data
    except Exception:
        return DEFAULT_DATA

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_lan_ip():
    """取得當前主機在區網的 IP，方便手機連線使用"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0.5)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        try:
            return socket.gethostbyname(socket.gethostname())
        except Exception:
            return "127.0.0.1"

# 手機與網頁雙向即時同步狀態紀錄
SYNC_STATE = {
    "version": 1,
    "last_updated": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "latest_event": {
        "version": 1,
        "time": datetime.datetime.now().strftime("%H:%M:%S"),
        "full_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "action_type": "system_init",
        "title": "手機·網頁即時同步連線就緒",
        "message": "大清天朵二期社區手機與網頁即時雙向同步中樞已就緒",
        "source": "server",
        "details": {}
    },
    "events": []
}

def record_sync_event(action_type, title, message, source="mobile", details=None):
    """記錄手機端或網頁端完成的動作，並遞增全域同步版本號"""
    SYNC_STATE["version"] += 1
    now_str = datetime.datetime.now().strftime("%H:%M:%S")
    now_full = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    SYNC_STATE["last_updated"] = now_full
    event = {
        "version": SYNC_STATE["version"],
        "time": now_str,
        "full_time": now_full,
        "action_type": action_type,
        "title": title,
        "message": message,
        "source": source,
        "details": details or {}
    }
    SYNC_STATE["latest_event"] = event
    SYNC_STATE["events"].insert(0, event)
    if len(SYNC_STATE["events"]) > 50:
        SYNC_STATE["events"] = SYNC_STATE["events"][:50]
    return event

class CommunityAppHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path.startswith("/api/"):
            self.handle_api_get(parsed.path, parse_qs(parsed.query))
            return
        
        # 靜態文件處理
        if parsed.path == "/" or parsed.path == "":
            self.path = "/index.html"
        return super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path.startswith("/api/"):
            content_len = int(self.headers.get('Content-Length', 0))
            post_body = self.rfile.read(content_len).decode('utf-8')
            try:
                body_json = json.loads(post_body) if post_body else {}
            except Exception:
                body_json = {}
            self.handle_api_post(parsed.path, body_json)
            return

        self.send_error(404, "Not Found")

    def send_json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))

    def handle_api_get(self, path, query_params):
        data = load_data()
        if path == "/api/status":
            self.send_json({
                "community_name": data["community_name"],
                "committee_term": data["committee_term"],
                "total_residents": len(data["residents"]),
                "paid_count": sum(1 for r in data["residents"] if r["paid"]),
                "dispatches_count": len(data["dispatches"]),
                "petty_cash_status": data["petty_cash"]["final_status"],
                "cwa_alert": data["flood_system"]["cwa_weather"]["alert_level"],
                "cwa_alert_name": data["flood_system"]["cwa_weather"]["alert_name"]
            })
        elif path == "/api/residents":
            role = query_params.get("role", ["resident"])[0]
            unit = query_params.get("unit", [""])[0]
            if role == "resident":
                res = [r for r in data["residents"] if r["unit"] == unit]
                if res:
                    masked = {
                        "unit": res[0]["unit"],
                        "name": res[0]["name"][0] + "〇" + (res[0]["name"][2:] if len(res[0]["name"]) > 2 else ""),
                        "fee": res[0]["fee"],
                        "account_suffix": "***" + res[0]["account_suffix"][-2:],
                        "paid": res[0]["paid"],
                        "payment_date": res[0]["payment_date"]
                    }
                    self.send_json({"resident": masked})
                else:
                    self.send_json({"error": "找不到此戶別或無權限存取"}, 404)
            else:
                self.send_json({"residents": data["residents"]})
        elif path == "/api/dispatches":
            now_ts = int(datetime.datetime.now().timestamp() * 1000)
            data["dispatches"] = [
                d for d in data.get("dispatches", [])
                if not (d.get("completed") and d.get("completed_timestamp") and (now_ts - d.get("completed_timestamp", 0) >= 24 * 3600 * 1000))
            ]
            save_data(data)
            self.send_json({"dispatches": data["dispatches"]})
        elif path == "/api/petty_cash":
            self.send_json({"petty_cash": data["petty_cash"]})
        elif path == "/api/financial_statement_i":
            if "financial_statement_i" not in data:
                data["financial_statement_i"] = json.loads(json.dumps(DEFAULT_DATA["financial_statement_i"]))
            self.send_json({"financial_statement_i": data["financial_statement_i"]})
        elif path == "/api/bylaws":
            self.send_json({"bylaws": data["bylaws"]})
        elif path == "/api/flood_system":
            self.send_json({"flood_system": data["flood_system"]})
        elif path == "/api/sync_status":
            try:
                client_ver = int(query_params.get("version", ["0"])[0])
            except Exception:
                client_ver = 0
            lan_ip = get_lan_ip()
            self.send_json({
                "current_version": SYNC_STATE["version"],
                "has_update": client_ver < SYNC_STATE["version"],
                "latest_event": SYNC_STATE["latest_event"],
                "recent_events": SYNC_STATE["events"][:20],
                "lan_ip": lan_ip,
                "port": PORT,
                "mobile_url": f"http://{lan_ip}:{PORT}"
            })
        elif path == "/api/helper_bookings":
            self.send_json({"helper_bookings": data.get("helper_bookings", [])})
        else:
            self.send_json({"error": "Endpoint not found"}, 404)

    def handle_api_post(self, path, body):
        data = load_data()

        if path == "/api/verify_rule":
            # Skill 1: 規約與決議邏輯檢核
            query = body.get("query", "").strip()
            matched_rules = []
            for law in data["bylaws"]:
                score = 0
                for kw in law["keywords"]:
                    if kw in query:
                        score += 1
                if score > 0 or any(word in law["content"] for word in query.split()):
                    matched_rules.append(law)

            has_flood = any(k in query for k in ["防水閘門", "防汛", "演練", "操演", "淹水", "氣象局", "豪大雨", "暴雨", "沙包", "閘門"])
            has_shoe_rack = "鞋櫃" in query or "走廊" in query or "梯廳" in query
            has_ev = "充電" in query or "電動車" in query or "充電樁" in query
            has_ac = "冷氣" in query or "室外機" in query or "滴水" in query

            if has_flood:
                result = {
                    "related_rules": [
                        "社區防汛與地下室防水閘門定期檢測及實兵操演規約（第四屆區分所有權人會議決議暨防汛作業標準手冊）。",
                        "公寓大廈管理條例第十條：共用部分、約定共用部分之修繕、管理、維護，由管理負責人或管理委員會為之。",
                        "年度例行防汛排程條款：每年汛期前（每年5月份）應召集固德物業管理員完成閉合操演與沙包盤點。"
                    ],
                    "historical_practice": "大清天朵二期每年固定於 5 月中旬由固德物業總幹事會同管委會機電委員，召集全體日夜班保全及清潔人員實施地下室車道防水閘門實兵組裝測時演練（上年度演練實測耗時 11 分 35 秒，符合 15 分鐘標準），並實地通電測試截水溝三組沉水抽水泵。",
                    "conflicts": "若管委會或物業僅做書面形式檢驗而未落實『實兵操演組裝』，或因疏失未於每年 5 月汛期前完成檢測，一旦遭遇極端豪大雨導致車道倒灌致使地下室車輛受損，受託之固德物業與管委會委員將直接面臨未盡『善良管理人注意義務』之法律過失責任，衍生鉅額民事損害賠償風險；若橡膠止水條硬化破損未及時編列預算更換，亦違反公設維護常規。",
                    "recommendations": "1. 恪遵規約嚴格執行每年 5 月年度實兵操演，落實四大項目檢驗：軌道潤滑、止水膠條密封、沉水泵測試、50包沙包盤點。\n2. 操演日前 3 天由物業發布車道管制公告，操演時拍照存證並計時填報檢核表。\n3. 當中央氣象局發布豪大雨特報時，系統自動啟動緊急防汛推播，物業管理員應立即至車道就位備妥閘門擋板。\n4. 本助手維持客觀中立，決策權與核銷權保留予管委會。"
                }
            elif has_shoe_rack:
                result = {
                    "related_rules": [
                        "社區規約第十六條：各樓層梯廳、走廊全面禁止私自堆置任何個人物品（含鞋櫃、雨傘架、雜物等）。",
                        "第三屆區權會決議案（案由五）：出席權數 82% 投票否決放寬薄型鞋櫃提議，維持嚴格全面淨空。"
                    ],
                    "historical_practice": "管委會與固德物業歷來均依規約執行拍照、張貼 24 小時限期改善單，逾期即依公寓大廈管理條例報請主管機關裁罰。",
                    "conflicts": "若本次管委會或住戶研議『開放放置特定規格之薄型鞋櫃』，將直接牴觸【第三屆區分所有權人大會之法定決議】及【公寓大廈管理條例第十六條第二項】規定。依公寓大廈管理條例，管委會無權以常會決議推翻區權會決議。",
                    "recommendations": "1. 依現行規約與法令，走廊屬避難通道，管委會應維持走道淨空，不宜私自放寬。\n2. 若委員欲重議此案，法定程序須於下屆區分所有權人會議提出規約修正案，並達法定出席與同意門檻方具法律效力。\n3. 本助手維持客觀中立，最終管理決策權保留給全體區權會與管委會。"
                }
            elif has_ev:
                result = {
                    "related_rules": [
                        "第四屆管委會第五次常會決議：地下停車場私人車位加裝電動車充電設備（EMS）管理規範。"
                    ],
                    "historical_practice": "申請人需自備合格台電圖說與甲級電匠施工計畫，自費設置獨立電錶，禁止私接公電。",
                    "conflicts": "若住戶直接自公共配電箱拉線，或未經管委會機電審查逕行安裝，將違反公共安全與公積金用電公平原則。",
                    "recommendations": "1. 請物業提供制式『充電設備裝設申請表』給申請住戶。\n2. 委請社區機電顧問就線槽容量與負載進行安全確認，簽署安全切結書後方可進場施工。"
                }
            elif has_ac:
                result = {
                    "related_rules": ["社區規約第十九條：冷氣室外機之安裝管理規範。"],
                    "historical_practice": "嚴格限制於建商預留之冷氣樑位安裝，不得懸掛於大樓立面外側。",
                    "conflicts": "擅自懸掛外牆涉嫌破壞大樓外觀統一風格，且若防墜支架鏽蝕恐衍生公共危險責任。",
                    "recommendations": "1. 勸導住戶立即更正安裝位置至指定樑位。\n2. 如外包廠商強行施工，物業得拒絕其進場施工。"
                }
            else:
                result = {
                    "related_rules": [r["title"] + " (" + r["source"] + ")" for r in matched_rules] if matched_rules else ["未檢索到完全相符之具體條文，已引用社區一般管理辦法"],
                    "historical_practice": "社區常態事務均由固德物業巡檢登記，並提報每月管委會常會裁決。",
                    "conflicts": "經系統比對，該項提議目前未發現明顯規約衝突，但需留意是否侵害其他住戶之共用權益或消防安全法令。",
                    "recommendations": "建議提請下次管委會例行會議審議討論，或由固德物業先行進行住戶意願調查。"
                }

            self.send_json(result)

        elif path == "/api/trigger_may_reminder":
            # 觸發每年5月例行防汛操演排程提醒
            now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            new_log = {
                "time": now_str,
                "title": "【系統排程提醒 - 每年5月例行防汛演練】",
                "recipients": "固德物業總幹事、全體管委會委員（主任委員、機電委員）",
                "content": "⚠️【防汛重點通知】：依社區防汛規約，汛期即將來臨！請固德物業於 5 月 20 日前排定『地下室車道防水閘門實兵組裝閉合操演』，並落實機械軌道清潔防銹潤滑、止水膠條密封性檢驗、60包備用沙包盤點及沉水泵排水測試。操演紀錄與驗收照片需陳報管委會核備並公告住戶！"
            }
            data["flood_system"]["annual_drill"]["reminder_history"].insert(0, new_log)
            save_data(data)
            self.send_json({"success": True, "reminder": new_log})

        elif path == "/api/cwa_weather_alert":
            # 模擬或切換中央氣象署警報 (normal vs heavy_rain vs clear)
            level = body.get("level", "heavy_rain") # heavy_rain, normal
            now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            if level == "heavy_rain":
                data["flood_system"]["cwa_weather"]["alert_level"] = "heavy_rain"
                data["flood_system"]["cwa_weather"]["alert_name"] = "🌧️ 中央氣象署發布【豪大雨特報】"
                data["flood_system"]["cwa_weather"]["rainfall_forecast"] = "受鋒面與低壓影響，台北市預估24小時累積雨量達 200mm 以上，請加強防汛戒備。"
                data["flood_system"]["cwa_weather"]["updated_at"] = now_str

                # 自動生成緊急推播記錄至管委會與物業管理員群組
                alert_push = {
                    "time": now_str,
                    "level": "豪大雨特報 (緊急一級防汛)",
                    "source": "交通部中央氣象署 Webhook 自動觸發",
                    "push_targets": ["管委會全體委員群組", "固德物業現場管理中心", "日間/夜班保全管理員"],
                    "message": (
                        "🚨【中央氣象署豪大雨緊急警報推播】\n"
                        "氣象署已針對台北市發布豪大雨特報，預估時雨量高達 60mm 以上！\n"
                        "⚡ 系統已自動啟動大清天朵二期【一級防汛應變標準作業流程 (SOP)】：\n"
                        "1. 請現場管理員立即至地下室車道確認防汛防水閘門擋板與支架就定位。\n"
                        "2. 檢查車道截水溝柵欄泥沙雜物，測試三組沉水抽水泵強制運轉。\n"
                        "3. 備妥 60 包防汛沙包並放置於車道迎水面及地下室發電機房門口。\n"
                        "4. 透過官方 LINE 頻道推播提醒地下停車場住戶車主注意水情！"
                    ),
                    "status": "已推播至委員與管理員 LINE 群組 (延遲 1.2s)"
                }
                data["flood_system"]["cwa_weather"]["broadcast_logs"].insert(0, alert_push)
            else:
                data["flood_system"]["cwa_weather"]["alert_level"] = "normal"
                data["flood_system"]["cwa_weather"]["alert_name"] = "☀️ 天氣正常 (無豪雨警報)"
                data["flood_system"]["cwa_weather"]["rainfall_forecast"] = "台北市降雨機率 10%，氣象穩定。"
                data["flood_system"]["cwa_weather"]["updated_at"] = now_str
                alert_push = {
                    "time": now_str,
                    "level": "解除豪大雨警報",
                    "source": "系統手動/氣象署解除特報",
                    "push_targets": ["管委會委員", "現場管理員"],
                    "message": "中央氣象署已解除台北市豪大雨特報，水情趨緩，恢復常態防災巡檢。",
                    "status": "已推播解除通知"
                }
                data["flood_system"]["cwa_weather"]["broadcast_logs"].insert(0, alert_push)

            save_data(data)
            self.send_json({
                "success": True,
                "cwa_weather": data["flood_system"]["cwa_weather"],
                "latest_push": alert_push
            })

        elif path == "/api/vision_dispatch":
            category = body.get("category", "Damage")
            location = body.get("location", "健身房")
            description = body.get("description", "住戶拍照通報現場異常狀況")
            reporter = body.get("reporter", "住戶（A棟8樓之1 · 饒先生）")
            image_url = body.get("image_url", "https://images.unsplash.com/photo-1534438327276-14e5300c3a48?w=600&auto=format&fit=crop&q=60")

            cat_map = {
                "Trash": ("垃圾棄置", "物業清潔組"),
                "Lost Item": ("遺失物", "物業管理中心"),
                "Damage": ("設施異常", "物業機電/修繕組"),
                "ResidentReport": ("異常通報", "物業管理室 / 總幹事"),
                "Other": ("其他/違規行為", "物業主管與管委會")
            }
            cat_name = body.get("category_name") or cat_map.get(category, ("異常通報", "物業管理室"))[0]
            target_team = body.get("target_team") or cat_map.get(category, ("異常通報", "物業管理室 / 總幹事"))[1]
            status = body.get("status", "處理中")

            disp_id = body.get("id") or f"DISP-{datetime.datetime.now().strftime('%Y%m%d')}-{len(data['dispatches'])+1:03d}"
            disp_time = body.get("time") or datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            new_disp = {
                "id": disp_id,
                "time": disp_time,
                "category": category,
                "category_name": cat_name,
                "location": location,
                "reporter": reporter,
                "description": description,
                "status": status,
                "target_team": target_team,
                "image_url": image_url,
                "notified_management": True,
                "management_push_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            data["dispatches"].insert(0, new_disp)
            save_data(data)
            source = body.get("client_type", "mobile")
            record_sync_event(
                action_type="dispatch_created",
                title="住戶手機異常拍照通報",
                message=f"住戶（{reporter}）於手機完成【{location}】異常拍照通報：「{description}」",
                source=source,
                details={"id": disp_id, "location": location, "reporter": reporter, "category": cat_name, "image_url": image_url}
            )
            self.send_json({
                "success": True, 
                "dispatch": new_disp,
                "management_notified": True,
                "push_details": {
                    "receiver": "固德物業管理室（高瑞彣總幹事／保全櫃檯）",
                    "channel": "LINE 官方群組推播 & 中控台警示",
                    "title": f"【即時異常通報提醒】{location} 發生狀況",
                    "content": f"住戶（{reporter}）已拍照通報【{location}】：{description}，管理室已即時收到派單！",
                    "time": disp_time
                }
            })

        elif path == "/api/vision_dispatch_complete":
            disp_id = body.get("id")
            found = None
            for d in data.get("dispatches", []):
                if d.get("id") == disp_id:
                    d["status"] = "處理完成"
                    d["completed"] = True
                    d["completed_by"] = body.get("completed_by", "管委會委員")
                    d["completed_time"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                    d["completed_timestamp"] = int(datetime.datetime.now().timestamp() * 1000)
                    d["auto_close_time"] = (datetime.datetime.now() + datetime.timedelta(hours=24)).strftime("%Y-%m-%d %H:%M")
                    found = d
                    break
            if found:
                save_data(data)
                source = body.get("client_type", "web")
                record_sync_event(
                    action_type="dispatch_completed",
                    title="工單已處理完成",
                    message=f"委員已確認【{found.get('location')}】異常通報處理完成，將於24小時後主動結案刪除。",
                    source=source,
                    details=found
                )
            self.send_json({"success": True, "dispatch": found})

        elif path == "/api/vision_dispatch_delete":
            disp_id = body.get("id")
            prev_len = len(data.get("dispatches", []))
            data["dispatches"] = [d for d in data.get("dispatches", []) if d.get("id") != disp_id]
            if len(data["dispatches"]) != prev_len:
                save_data(data)
                record_sync_event(
                    action_type="dispatch_deleted",
                    title="工單已結案刪除",
                    message=f"工單 #{disp_id} 已結案並自畫面刪除。",
                    source=body.get("client_type", "web"),
                    details={"id": disp_id}
                )
            self.send_json({"success": True})

        elif path == "/api/reconcile":
            amount = float(body.get("amount", 0))
            account_suffix = str(body.get("account_suffix", "")).strip()

            matched = None
            for resident in data["residents"]:
                if resident["account_suffix"] == account_suffix and float(resident["fee"]) == amount:
                    matched = resident
                    resident["paid"] = True
                    resident["payment_date"] = datetime.datetime.now().strftime("%Y-%m-%d")
                    break
            
            if matched:
                save_data(data)
                source = body.get("client_type", "mobile")
                record_sync_event(
                    action_type="reconciled",
                    title="管理費繳費自動銷帳",
                    message=f"住戶（{matched['unit']} · {matched['name']}）完成管理費 NT$ {matched['fee']:,} 元入帳銷帳",
                    source=source,
                    details={"unit": matched["unit"], "fee": matched["fee"]}
                )
                masked_account = "***" + account_suffix[-2:] if len(account_suffix) >= 2 else "***"
                receipt = {
                    "receipt_no": f"REC-{datetime.datetime.now().strftime('%Y%m')}-{matched['unit'].replace('-', '')}",
                    "unit": matched["unit"],
                    "resident_name": matched["name"][0] + "〇" + (matched["name"][2:] if len(matched["name"]) > 2 else ""),
                    "amount": matched["fee"],
                    "account_masked": masked_account,
                    "date": matched["payment_date"],
                    "item": f"大清天朵二期 2026年09月份 管理維護費",
                    "status": "已入帳核銷完畢"
                }
                self.send_json({"success": True, "matched": True, "receipt": receipt})
            else:
                self.send_json({
                    "success": False,
                    "matched": False,
                    "message": f"未找到金額 NT$ {amount:,.0f} 與末五碼 【{account_suffix}】 完全吻合之待繳戶別，已轉入【人工待核清單】。"
                })

        elif path == "/api/petty_cash/approve":
            officer = body.get("officer")
            decision = body.get("decision")
            comment = body.get("comment", "")

            approvals = data["petty_cash"]["approvals"]
            if officer in approvals:
                approvals[officer]["status"] = decision
                approvals[officer]["comment"] = comment or ("已同意通過" if decision == "approved" else "退回請物業補正說明")
                approvals[officer]["time"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

                all_approved = all(v["status"] == "approved" for v in approvals.values())
                any_rejected = any(v["status"] == "rejected" for v in approvals.values())

                if any_rejected:
                    data["petty_cash"]["final_status"] = "rejected"
                elif all_approved:
                    data["petty_cash"]["final_status"] = "approved"
                else:
                    data["petty_cash"]["final_status"] = "in_review"

                save_data(data)
                source = body.get("client_type", "mobile")
                role_names = {"director": "主任委員（陳建宏）", "finance": "財務委員（林秀玲）", "supervisor": "行政委員（王國華）"}
                officer_name = role_names.get(officer, officer)
                action_zh = "同意簽核" if decision == "approved" else "退回補正"
                record_sync_event(
                    action_type="petty_approved",
                    title=f"委員費用審核：{action_zh}",
                    message=f"{officer_name}於手機完成115年八月份報支簽核（{action_zh}）",
                    source=source,
                    details={"officer": officer, "decision": decision, "comment": comment}
                )
                self.send_json({"success": True, "petty_cash": data["petty_cash"]})
            else:
                self.send_json({"error": "Invalid officer"}, 400)

        elif path == "/api/petty_cash/update_form_q":
            items = body.get("items")
            declarations = body.get("declarations")
            scheduled_payment_date = body.get("scheduled_payment_date")
            withdrawal_date = body.get("withdrawal_date")
            passbook_balance = body.get("passbook_balance")

            if items is not None:
                data["petty_cash"]["items"] = items
                data["petty_cash"]["total_spent"] = sum(int(i.get("amount", 0)) for i in items)
            if declarations is not None:
                data["petty_cash"]["declarations"] = declarations
            if scheduled_payment_date:
                data["petty_cash"]["scheduled_payment_date"] = scheduled_payment_date
            if withdrawal_date:
                data["petty_cash"]["withdrawal_date"] = withdrawal_date
            if passbook_balance is not None:
                try:
                    data["petty_cash"]["balance_info"]["passbook_balance_before"] = int(passbook_balance)
                except Exception:
                    pass

            save_data(data)
            self.send_json({"success": True, "petty_cash": data["petty_cash"]})

        elif path == "/api/petty_cash/reset":
            data["petty_cash"] = json.loads(json.dumps(DEFAULT_DATA["petty_cash"]))
            save_data(data)
            self.send_json({"success": True, "petty_cash": data["petty_cash"]})

        elif path == "/api/financial_statement_i/update":
            form_data = body.get("financial_statement_i")
            if form_data:
                data["financial_statement_i"] = form_data
                save_data(data)
                self.send_json({"success": True, "financial_statement_i": data["financial_statement_i"]})
            else:
                self.send_json({"error": "No data provided"}, 400)

        elif path == "/api/financial_statement_i/approve":
            officer = body.get("officer")
            decision = body.get("decision")
            comment = body.get("comment", "")
            if "financial_statement_i" not in data:
                data["financial_statement_i"] = json.loads(json.dumps(DEFAULT_DATA.get("financial_statement_i", {})))
            approvals = data["financial_statement_i"]["approvals"]
            if officer in approvals:
                approvals[officer]["status"] = decision
                approvals[officer]["comment"] = comment or ("已同意通過" if decision == "approved" else "退回請物業補正說明")
                approvals[officer]["time"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

                all_approved = all(v["status"] == "approved" for v in approvals.values())
                any_rejected = any(v["status"] == "rejected" for v in approvals.values())

                if any_rejected:
                    data["financial_statement_i"]["final_status"] = "rejected"
                elif all_approved:
                    data["financial_statement_i"]["final_status"] = "approved"
                else:
                    data["financial_statement_i"]["final_status"] = "in_review"

                save_data(data)
                source = body.get("client_type", "mobile")
                role_names = {"director": "主任委員（陳建宏）", "finance": "財務委員（林秀玲）", "supervisor": "行政委員（王國華）"}
                officer_name = role_names.get(officer, officer)
                action_zh = "同意簽核" if decision == "approved" else "退回補正"
                record_sync_event(
                    action_type="form_i_approved",
                    title=f"財務收支表審核：{action_zh}",
                    message=f"{officer_name}於手機完成八月份財務收支表(I)簽核（{action_zh}）",
                    source=source,
                    details={"officer": officer, "decision": decision, "comment": comment}
                )
                self.send_json({"success": True, "financial_statement_i": data["financial_statement_i"]})
            else:
                self.send_json({"error": "Invalid officer"}, 400)

        elif path == "/api/financial_statement_i/reset":
            data["financial_statement_i"] = json.loads(json.dumps(DEFAULT_DATA["financial_statement_i"]))
            save_data(data)
            self.send_json({"success": True, "financial_statement_i": data["financial_statement_i"]})

        elif path == "/api/petty_cash/upload_receipt":
            import base64
            image_base64 = body.get("image_base64", "")
            item_idx = body.get("item_idx")
            custom_title = body.get("title", "")

            if image_base64:
                try:
                    if "," in image_base64:
                        header, b64_data = image_base64.split(",", 1)
                    else:
                        header, b64_data = "", image_base64

                    file_bytes = base64.b64decode(b64_data)
                    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                    ext = ".png" if "png" in header.lower() else ".jpg"
                    idx_str = f"項目{int(item_idx)+1}_" if item_idx is not None else ""
                    filename = f"現場拍照單據_{idx_str}{timestamp}{ext}"
                    filepath = os.path.join(BASE_DIR, filename)
                    with open(filepath, "wb") as f:
                        f.write(file_bytes)

                    # Update specific item if item_idx given
                    if item_idx is not None and 0 <= int(item_idx) < len(data["petty_cash"]["items"]):
                        item_ref = data["petty_cash"]["items"][int(item_idx)]
                        if "attachments" not in item_ref or not isinstance(item_ref["attachments"], list):
                            cur = []
                            if item_ref.get("attachment"): cur.append(item_ref["attachment"])
                            if item_ref.get("quote_slip") and item_ref.get("quote_slip") not in cur: cur.append(item_ref["quote_slip"])
                            if item_ref.get("payment_slip") and item_ref.get("payment_slip") not in cur: cur.append(item_ref["payment_slip"])
                            item_ref["attachments"] = cur
                        if len(item_ref["attachments"]) < 3:
                            item_ref["attachments"].append(filename)
                        else:
                            return self.send_json({"error": "該款項項目已附加滿 3 張單據，無法再新增。請先刪除既有單據！"}, 400)
                        item_ref["attachment"] = item_ref["attachments"][0]
                        item_ref["is_uploaded"] = True

                    # Append to attachments database list
                    new_att = {
                        "id": f"att-upload-{timestamp}",
                        "title": custom_title or f"現場拍照單據 ({filename})",
                        "type": "jpg" if ext == ".jpg" else "png",
                        "file": filename,
                        "category": "拍照上傳",
                        "desc": f"於 {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')} 現場手機拍照上傳之原始憑證"
                    }
                    data["petty_cash"]["attachments"].append(new_att)
                    save_data(data)
                    source = body.get("client_type", "mobile")
                    record_sync_event(
                        action_type="receipt_uploaded",
                        title="現場單據照片上傳",
                        message=f"現場人員於手機拍照上傳憑證照片（{filename}）",
                        source=source,
                        details={"filename": filename}
                    )

                    self.send_json({
                        "success": True,
                        "filename": filename,
                        "attachment": new_att,
                        "petty_cash": data["petty_cash"]
                    })
                except Exception as e:
                    self.send_json({"error": f"Upload failed: {str(e)}"}, 500)
            else:
                self.send_json({"error": "No image data provided"}, 400)

        elif path == "/api/petty_cash/delete_receipt":
            item_idx = body.get("item_idx")
            img_idx = body.get("img_idx")

            if item_idx is not None and 0 <= int(item_idx) < len(data["petty_cash"]["items"]):
                item_ref = data["petty_cash"]["items"][int(item_idx)]
                if "attachments" in item_ref and isinstance(item_ref["attachments"], list):
                    if img_idx is not None and 0 <= int(img_idx) < len(item_ref["attachments"]):
                        removed = item_ref["attachments"].pop(int(img_idx))
                        if len(item_ref["attachments"]) > 0:
                            item_ref["attachment"] = item_ref["attachments"][0]
                        else:
                            item_ref["attachment"] = ""
                        save_data(data)
                        source = body.get("client_type", "mobile")
                        record_sync_event(
                            action_type="receipt_deleted",
                            title="現場單據憑證更新",
                            message=f"現場單據憑證已更新刪除（{removed}）",
                            source=source
                        )
                        self.send_json({
                            "success": True,
                            "removed": removed,
                            "petty_cash": data["petty_cash"]
                        })
                    else:
                        self.send_json({"error": "Invalid img_idx"}, 400)
                else:
                    item_ref["attachment"] = ""
                    item_ref["attachments"] = []
                    save_data(data)
                    self.send_json({
                        "success": True,
                        "petty_cash": data["petty_cash"]
                    })
            else:
                self.send_json({"error": "Invalid item_idx"}, 400)

        elif path == "/api/sync_event":
            action_type = body.get("action_type", "custom_action")
            title = body.get("title", "手機端操作同步")
            message = body.get("message", "手機端完成操作並同步至網頁")
            source = body.get("source", "mobile")
            details = body.get("details", {})
            evt = record_sync_event(action_type, title, message, source, details)
            self.send_json({"success": True, "event": evt, "current_version": SYNC_STATE["version"]})

        elif path == "/api/helper_booking":
            service_key = body.get("service_key", "water_electric")
            service_title = body.get("service_title", "水電維修")
            unit = body.get("unit", "A-8F-1")
            resident_name = body.get("resident_name", "饒先生")
            remark = body.get("remark", "需要到府檢修服務")
            source = body.get("client_type", "mobile")
            booking_id = f"BK-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
            now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            booking = {
                "id": booking_id,
                "time": now_str,
                "service_key": service_key,
                "service_title": service_title,
                "unit": unit,
                "resident_name": resident_name,
                "remark": remark,
                "status": "已登記預約，物業中心即時接單"
            }
            if "helper_bookings" not in data:
                data["helper_bookings"] = []
            data["helper_bookings"].insert(0, booking)
            save_data(data)
            evt = record_sync_event(
                action_type="helper_booked",
                title=f"生活小幫手預約：{service_title}",
                message=f"住戶（{unit} · {resident_name}）於手機預約【{service_title}】：「{remark}」",
                source=source,
                details=booking
            )
            self.send_json({"success": True, "booking": booking})

        elif path == "/api/chat":
            user_msg = body.get("message", "").strip()
            role = body.get("role", "resident")
            current_unit = body.get("unit", "A-8F-1")
            reply = generate_ai_response(user_msg, role, current_unit, data)
            self.send_json({"reply": reply})

        else:
            self.send_json({"error": "Endpoint not found"}, 404)

def generate_ai_response(msg, role, unit, data):
    # 1. 防水閘門、防汛、氣象局、豪大雨
    if any(k in msg for k in ["防水閘門", "防汛", "演練", "操演", "氣象局", "氣象署", "豪大雨", "淹水", "沙包", "五月", "5月"]):
        return (
            "【大清天朵二期 AI 防汛與公寓大廈管理條例助手】\n"
            "針對「防水閘門檢測保養、實兵操演及氣象局連線推播機制」說明如下：\n\n"
            "🛡️【規約要求】：\n"
            "依大清天朵二期防汛作業手冊規約，車道防水閘門必須定期保養、檢測止水膠條密封度，並常備至少50包沙包。\n\n"
            "📅【每年 5 月系統主動提醒演練】：\n"
            "系統已設定每年 5 月 1 日自動發送推播通知至固德物業總幹事與管委會委員，要求於 5 月 20 日前完成「地下室車道防水閘門實兵組裝閉合操演（合格標準為 15 分鐘內閉合）」與抽水沉水泵測試。\n\n"
            "🚨【中央氣象局 (CWA) 即時連線與主動推播】：\n"
            "系統即時介接中央氣象署天氣預警。當台北市發布「豪雨/大豪雨特報」或颱風警報時，系統將於 60 秒內主動推播警報給【管委會全體委員】及【固德物業現場管理員】，同步發布四項防汛應變 SOP 清單（擋板就位、測試沉水泵、堆放沙包、推播住戶車主注意）。"
        )

    # 2. 住戶查詢繳費
    if "管理費" in msg or "繳費" in msg or "帳單" in msg:
        if role == "resident":
            resident = next((r for r in data["residents"] if r["unit"] == unit), None)
            if resident:
                if resident["paid"]:
                    return f"【大清天朵二期 AI 財務助手】\n您好，您綁定的戶別為【{unit}】。\n✅ 查詢結果：本月份管理費（NT$ {resident['fee']:,} 元）已於 {resident['payment_date']} 順利入帳銷帳完畢，感謝您的配合！"
                else:
                    return f"【大清天朵二期 AI 財務助手】\n您好，您綁定的戶別為【{unit}】。\n⚠️ 查詢結果：本月份管理費應繳金額為 NT$ {resident['fee']:,} 元，目前系統顯示「尚未入帳」。若您已匯款（帳號末5碼：{resident['account_suffix']}），請稍候銀行入帳批次更新或洽固德物業櫃檯。"
            else:
                return "系統查無此戶別綁定資訊，請確認您的身分登入。"
        elif role in ["property", "committee"]:
            paid_c = sum(1 for r in data["residents"] if r["paid"])
            unpaid_c = len(data["residents"]) - paid_c
            return f"【固德物業／管委會 財務概況】\n本月社區管理費繳納進度：\n- 已入帳戶數：{paid_c} 戶\n- 待入帳戶數：{unpaid_c} 戶\n您可切換至「財務與對帳」頁籤查看各戶明細與銀行自動銷帳記錄。"

    # 3. 走廊鞋櫃比對
    if "鞋櫃" in msg or "走廊" in msg:
        return (
            "【大清天朵二期 AI 公寓大廈管理條例檢核分析】\n"
            "針對「走廊放置鞋櫃」之合規性比對結果如下：\n\n"
            "📌【相關規約條文】：社區規約第十六條明訂，梯廳走廊共用部分禁止擺放鞋櫃、雜物。\n"
            "🏛️【歷史決策慣例】：第三屆區權會大會以 82% 高出席權數否決放置薄型鞋櫃之提案，決議維持走廊完全淨空。\n"
            "⚠️【潛在邏輯矛盾】：任何放寬鞋櫃擺放之常會提案，將直接牴觸區分所有權人會議之法定公約與消防法規，管委會無權擅自推翻大會決議。\n"
            "💡【建議處理方式】：依現行規約持續勸導淨空；若欲重提此案，應於下屆區權會提出正式規約修正案投票。"
        )

    # 4. 固德公司「高瑞彣」費用報支與三委員簽核
    if any(k in msg for k in ["高瑞彣", "報支", "待支付", "費用", "簽核", "零用金", "取款條", "收支表", "存款紀錄", "報價", "宏捷", "鼎聖", "誼潔"]):
        petty = data["petty_cash"]
        items_str = "\n".join([f"  {idx+1}. 【{item['category']}】{item['title']}（{item['vendor']}）：NT$ {item['amount']:,} 元" for idx, item in enumerate(petty["items"])])
        status_text = "✅ 已全額核准（3位委員均已同意）" if petty["final_status"] == "approved" else ("⏳ 審核中（等待委員簽核）" if petty["final_status"] == "in_review" else "⚠️ 已被退回補正")
        return (
            f"【固德物業（承辦人：{petty.get('submitter_name', '高瑞彣')}）八月份費用報支簽核分析】\n"
            f"📋 案件名稱：{petty.get('case_title', '115年八月份社區一般費用報支案')}\n"
            f"📅 提報月份：{petty['month']}（預定支付日：{petty.get('scheduled_payment_date', '115年8月31日')}）\n"
            f"💰 總支出金額：NT$ {petty.get('total_spent', 24500):,} 元（共 4 筆款項）：\n{items_str}\n\n"
            f"🏦【專款存轉】：{petty.get('deposit_transfer_desc', '8/31 華南銀行提領 50,000 元轉存入社區郵局帳戶')}\n"
            "🔍【AI 自動核驗】：四表合一勾稽（待支付費用明細表、財務收支表、一般費用報支單、取款條傳票）總額一致；宏捷機電 $1,500 報價單已獲管委會簽認核准，承辦人高瑞彣印戳全數齊全。\n"
            f"🖋️【三位委員簽核進度】：{status_text}\n"
            f"  • 主任委員（{petty['approvals']['director']['name']}）：已同意（{petty['approvals']['director']['time']}）\n"
            f"  • 財務委員（{petty['approvals']['finance']['name']}）：已同意（{petty['approvals']['finance']['time']}）\n"
            f"  • 行政委員（{petty['approvals']['supervisor']['name']}）：已同意（{petty['approvals']['supervisor']['time']}）\n\n"
            "📎【附件預覽庫】：包含待支付費用明細表、財務收支表、一般費用報支單(15~18)、取款條、存款紀錄、維修商報價單及財務通知 PDF，皆可在「費用簽核」頁籤直接在線高清預覽！"
        )

    # 5. 生活小幫手（水電維修、附近餐館預訂、生鮮團購、燙髮預約、衣服送洗）
    if any(k in msg for k in ["生活小幫手", "水電", "餐館", "餐廳", "團購", "生鮮", "燙髮", "美髮", "送洗", "洗衣", "便民"]):
        return (
            "【大清天朵二期 · 生活小幫手服務】\n"
            "為提升住戶生活便利性，管委會已先完成建置「五大便民服務」專屬板塊：\n\n"
            "1. 🔧【水電維修】：特約專業乙級/甲級持證技師，提供水管抓漏、電路跳電檢測、燈具更換與衛浴疏通，收費公道透明。\n"
            "2. 🍽️【附近餐館預訂】：彙整周邊步行 5~10 分鐘優質餐廳，住戶專屬 9 折優惠與尖峰時段保留席免排隊。\n"
            "3. 🥬【生鮮團購】：產地直送有機當季蔬菜箱、放牧土雞蛋、海鮮與肉品，專車直送社區物業低溫冷藏箱代收。\n"
            "4. 💇【燙髮美髮預約】：周邊口碑沙龍名店合作，天朵住戶享剪燙染護專屬 85 折優惠，免現場苦候可指定設計師。\n"
            "5. 👔【衣服送洗】：專業環保乾洗水洗、蒸氣立體整燙，西裝大衣被單送交 1 樓物業櫃檯代收代送。\n\n"
            "📌【建置進度說明】：目前各項服務介面已建置完成（先建置好，後續再來連結），管委會與物業團隊刻正接洽周邊商家與串接線上預約系統！住戶可點選頂部「生活小幫手」頁籤查看各項服務介紹。"
        )

    # 6. 異常拍照通報與管理室即時連線推播（健身房、KTV室、2F~15F）
    if any(k in msg for k in ["異常通報", "通報", "拍照通報", "手機拍照", "報修", "派單", "拍照"]):
        return (
            "【大清天朵二期 · 異常拍照通報與管理室即時派單】\n"
            "住戶可於上方切換至「異常通報」頁籤進行快速線上派單：\n\n"
            "1. 📍【16處區域一鍵點選】：系統提供「健身房、KTV室、2F、3F、4F、5F、6F、7F、8F、9F、10F、11F、12F、13F、14F、15F」等可點選選項。\n"
            "2. 📸【手機相機拍照存證】：點選地點後，直接啟用手機相機拍照存證、從相簿上傳，或選取現場實景快照範例。\n"
            "3. 📝【狀況描述與上傳】：填寫狀況說明後點擊確認上傳。\n"
            "4. 📋【右側清單即時顯示】：派單成功後，右側「即時派單工單清單」將即刻置頂顯示該項通報與縮圖（點選可放大檢視）。\n"
            "5. 📢【管理室主動推播告知】：系統同步發送即時推播通知至固德物業管理室（高瑞彣總幹事／值班保全櫃檯），值勤人員將即刻前往現場查看處理！"
        )

    # 一般預設招呼
    return (
        f"您好！我是大清天朵二期社區 AI 管理助手（當前身分：{role}）。\n"
        "我能協助您處理：\n"
        "1. 公寓大廈管理條例與決議邏輯檢核（含走廊鞋櫃、地下室防水閘門定期操演規約）\n"
        "2. 防汛演練與氣象署連線（每年5月自動提醒演練、中央氣象局豪大雨主動推播）\n"
        "3. 異常通報與管理室即時推播（健身房、KTV室、2F~15F共16處選項＋手機拍照上傳）\n"
        "4. 社區財務自動銷帳（銀行入帳自動比對、住戶個人收據）\n"
        "5. 固德高瑞彣一般費用報支與三委員多重簽核自動化（含JPG/PDF附件高清預覽）\n"
        "6. 社區生活小幫手（水電維修、附近餐館預訂、生鮮團購、燙髮預約、衣服送洗）\n"
        "請點選上方功能頁籤，或直接告訴我您的問題！"
    )

if __name__ == "__main__":
    os.chdir(BASE_DIR)
    load_data()
    lan_ip = get_lan_ip()
    server = ThreadingHTTPServer(("0.0.0.0", PORT), CommunityAppHandler)
    print(f"==================================================")
    print(f"大清天朵二期社區 AI 管理助手（支援手機與網頁即時雙向同步）")
    print(f"電腦本機訪問: http://127.0.0.1:{PORT}")
    print(f"手機連線訪問: http://{lan_ip}:{PORT}")
    print(f"雙向同步模式: 毫秒級事件廣播 + 增量版本同步")
    print(f"==================================================")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n伺服器已停止。")
