from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from chatgpt import ChatGPT
from DB import Database

import os
import mysql.connector

line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
line_handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))
working_status = os.getenv("DEFALUT_TALKING", default = "true").lower() == "true"

app = Flask(__name__)
chatgpt = ChatGPT()

user_count = {}  # 建立一個 dict，用來儲存使用者的使用次數

# domain root
@app.route('/')
def home():
    return 'Hello, World!'

@app.route("/webhook", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']
    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    # handle webhook body
    try:
        line_handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@line_handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    global working_status
    working_status = True
    if event.message.type != "text":
        return
    user_id = event.source.user_id  # 取得使用者ID
    # if event.message.text == "請清除使用次數":  # 如果使用者傳來的訊息是 "XXXXX"，則清除該使用者的使用次數
    #     if user_id in user_count:
    #         user_count[user_id] = 0
    #         line_bot_api.reply_message(
    #             event.reply_token,
    #             TextSendMessage(text="已清除次數"))
    #     else:
    #         line_bot_api.reply_message(
    #             event.reply_token,
    #             TextSendMessage(text="你沒有使用次數"))
    # else:
    #     if user_id not in user_count:
    #         user_count[user_id] = 0
        
    #     # 如果使用者已經使用超過 3 次，回傳警告訊息
    #     if user_count[user_id] >= 3:
    #         line_bot_api.reply_message(
    #             event.reply_token,
    #             TextSendMessage(text="你已超過使用次數"))
    #     else:
    #         # 使用者使用次數 +1
    #         user_count[user_id] += 1
        
    # if user_count[user_id] > 3:  # 檢查使用次數是否達到限制
    #     line_bot_api.reply_message(
    #         event.reply_token,
    #         TextSendMessage(text="您已超過使用次數限制。"))

    if working_status:
        chatgpt.add_msg(f"Human:{event.message.text}?\n")
    
        db_host = os.getenv('DB_HOST')
        db_port = int(os.getenv('DB_PORT'))
        db_user = os.getenv('DB_USER')
        db_password = os.getenv('DB_PASSWORD')
        db_database = os.getenv('DB_DATABASE')
        # 資料庫連線
        db = Database(db_host, db_port, db_user, db_password, db_database)
        
        # 執行 資料庫 語法
        db.execute(
            'SELECT COUNT(`username`) as users, `frequency` FROM `gptest` WHERE `username` = %s', (user_id))
        # 顯示資料
        results = db.fetchall()
        
        if event.message.text == "請清除使用次數":
            db.execute("UPDATE `gptest` SET `frequency`= %s WHERE `username` = %s", ('0', user_id))
            db.commit()
            db.close()
            line_bot_api.reply_message(
                event.reply_token, TextSendMessage(text="你好！"))
            return
        
        
        if (results[0]['users'] == 0):
            db.execute(
                'INSERT INTO gptest (`username`, `frequency`) VALUES (%s, %s)', (user_id, 1))
            db.commit()  # 提交，否則不會新增到資料庫
        else:
            # 使用者發言次數超過 X 次時回覆訊息
            if int(results[0]['frequency']) >= 3:
                line_bot_api.reply_message(
                    event.reply_token, TextSendMessage(text="您已經發言超過 3 次了！"))
                return
            else:
                # 否則 該使用者輸入次數加1
                frequency = int(results[0]['frequency']) + 1
                # 更新 資料庫 使用者 次數
                db.execute(
                    'UPDATE `gptest` SET `frequency`= %s WHERE `username` = %s', (frequency, user_id))
                db.commit()  # 提交，否則不會新增到資料庫
        
        
                
        reply_msg = chatgpt.get_response().replace("AI:", "", 1)
        chatgpt.add_msg(f"AI:{reply_msg}\n")
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=reply_msg))
# def reset_frequency(input_str):
#     # 在這裡實作你的條件判斷邏輯
#     if input_str == "指定字串":
#         cursor = Database.cursor()
#         cursor.execute("UPDATE yourtable SET frequency = 0")
#         Database.commit()
#         cursor.close()

# 調用函式
# reset_frequency("要輸入的字串")

if __name__ == "__main__":
    app.run()
