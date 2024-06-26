#!/usr/bin/env python3
import asyncio
import math
import logging
import os
import json
import re
import requests

from datetime import datetime
from telegram import ParseMode, Update
from telegram.ext import CommandHandler, Filters, MessageHandler, Updater, ConversationHandler, CallbackContext
from prettytable import PrettyTable

TOKEN = os.environ.get("TOKEN")
APP_URL = os.environ.get("APP_URL")
PORT = int(os.environ.get('PORT', '8443'))


def create_table(data, type) -> PrettyTable:
    try:

       # Check if data is a string
        if isinstance(data, str):
            # If string, convert to Python object
            json_data = json.loads(data)
        elif isinstance(data, list):
           # If it's a list, use it directly
            json_data = data
        else:
            # If not a string or list, handle error or return
            raise ValueError("Invalid data format")
        
        if type == "topvalidators":
            table = PrettyTable()
            headers = ["Address", "Alias", "Voting Power", "Percentage" , "Uptime"]
            table.align["Address"] = "l"
            table.align["Voting Power"] = "l"
            table.align["Alias"] = "l"
            table.align["Percentage"] = "l"
            table.align["Uptime(%)"] = "l"
            table.title = "Top Validators"
            table.field_names = headers
            for entry in data:
                voting_power = round(entry['votingPower'] / 1000000, 2)
                truncated_address = entry['address'][:4] + "..." + entry['address'][-4:]
                table.add_row([truncated_address, entry['alias'], voting_power, entry['percentage'], entry['uptime'] ])
            return table
        elif type == "proposals":
            table = PrettyTable()
            headers = ["ID", "Kind", "Author", "Start Epoch", "End Epoch", "Grace Epoch", "Result"]
            table.title = "Proposals"
            table.field_names = headers
            for entry in data:
                author_account = entry.get("author", {}).get("Account", "")
                truncated_author_account = author_account[:4] + "..." + author_account[-4:]
                row = [
                    entry.get("id", ""),
                    entry.get("kind", ""),
                    truncated_author_account,
                    entry.get("start_epoch", ""),
                    entry.get("end_epoch", ""),
                    entry.get("grace_epoch", ""),
                    entry.get("result", "")
                ]
                table.add_row(row)
            return table
        elif type == "proposalpending":
            table = PrettyTable()
            headers = ["ID", "Kind", "Author", "Start Epoch", "End Epoch", "Grace Epoch", "Result"]
            table.title = "Pending Proposals"
            table.field_names = headers
            for entry in data:
                if entry.get("result", "") == "Pending":
                    author_account = entry.get("author", {}).get("Account", "")
                    truncated_author_account = author_account[:4] + "..." + author_account[-4:]       
                    row = [
                    entry.get("id", ""),
                    entry.get("kind", ""),
                    truncated_author_account,
                    entry.get("start_epoch", ""),
                    entry.get("end_epoch", ""),
                    entry.get("grace_epoch", ""),
                    entry.get("result", "")
                    ]
                    table.add_row(row)
            return table
        elif type == "votingproposals":
            table = PrettyTable()
            headers = ["ID", "Kind", "Author", "Start Epoch", "End Epoch", "Grace Epoch", "Result", "Yay", "Nay", "Abstain" ]
            table.title = "Voting Period - Proposals"
            table.field_names = headers
            for entry in data:
                if entry.get("result", "") == "VotingPeriod":
                    author_account = entry.get("author", {}).get("Account", "")
                    truncated_author_account = author_account[:4] + "..." + author_account[-4:]      
                    row = [
                    entry.get("id", ""),
                    entry.get("kind", ""),
                    truncated_author_account,
                    entry.get("start_epoch", ""),
                    entry.get("end_epoch", ""),
                    entry.get("grace_epoch", ""),
                    entry.get("result", ""),
                    round(float(entry.get("yay_votes", 0)) / 1000000, 2),
                    round(float(entry.get("nay_votes", 0)) / 1000000, 2),
                    round(float(entry.get("abstain_votes", 0)) / 1000000, 2)
                    ]
                    table.add_row(row)
            return table
        else:
            raise ValueError("Invalid type")
         
    except Exception as e:
        print(f"Error creating table: {e}")
        return None
    
def info(update: Update, context: CallbackContext) -> None:
    try:
       # Get information from endpoint /api/v1/chain/parameters
        parameter_api_url = 'https://it.api.namada.red/api/v1/chain/parameter'
        parameter_response = requests.get(parameter_api_url)
        
      # Get information from endpoint /api/v1/chain/info
        info_api_url = 'https://it.api.namada.red/api/v1/chain/info'
        info_response = requests.get(info_api_url)

         # Get information from endpoint /api/v1/chain/info
        info_cosapi_url = 'https://rpc-namada.cosmostation.io/status'
        info_response_status = requests.get(info_cosapi_url)
        
       # Check that both requests were successful
        if parameter_response.status_code == 200 and info_response.status_code == 200 and info_response_status.status_code == 200  :
            parameter_data = parameter_response.json()['parameters']
            info_data = info_response.json()
            info_response_status_data = info_response_status.json()['result']
            # Format values
            total_native_token_supply = int(parameter_data['total_native_token_supply']) / 1000000
            total_staked_native_token = int(parameter_data['total_staked_native_token']) / 1000000
            total_native_token_supply = round(total_native_token_supply, 2)
            total_staked_native_token = round(total_staked_native_token, 2)
            block_time = round(info_data['block_time'], 3)
            # Add latest_block_height and latest_block_time to the message
            latest_block_height = info_response_status_data['sync_info']['latest_block_height']
            latest_block_time = info_response_status_data['sync_info']['latest_block_time'][:-4]  # Remove milliseconds and 'Z' at the end
            
             
            
           # Create text messages with information from two sources
            # message = f"Epoch: {parameter_data['epoch']}\n"
            message = f"\n"
            message += f"Block time: {block_time}\n"
            message += f"Latest block height: {latest_block_height}\n"
            message += f"Latest block time (UTC): {latest_block_time}\n"
            # message += f"Last fetch block height: {info_data['last_fetch_block_height']}\n"
            message += f"Total transparent txs: {info_data['total_transparent_txs']}\n"
            message += f"Total shielded txs: {info_data['total_shielded_txs']}\n"
            message += f"Max validators: {parameter_data['max_validators']}\n"
            message += f"Total native token supply: {total_native_token_supply}\n"
            message += f"Total staked native token: {total_staked_native_token}\n"
            



            # Send Message
            update.effective_message.reply_text(message)
        else:
            update.effective_message.reply_text("Error get data from API.")
    except Exception as e:
        update.effective_message.reply_text(f"Lỗi: {e}")

# Hàm xử lý command /status
def topvalidators(update: Update, context: CallbackContext):
    api_url = 'https://namadafinder.cryptosj.net/sortedResults'
    response = requests.get(api_url)
    
    if response.status_code == 200:
        data = response.json()
        
        # Create PrettyTable
        table = create_table(data,"topvalidators")
        if table:
            # Split the table into batches
            count_rows = len(table._rows)
            batch_size = 25
            for start in range(0, count_rows, batch_size):
                end = min(start + batch_size, count_rows)


                # batch_table = table[start:end]
                # # Format the batch table as plain text
                # plain_text_table = batch_table.get_string()
                temp_table = table.get_string(start=start, end=end)
                part_temp_table = f'<pre>{temp_table}</pre>'
                # Send the plain text table as a message                
                # update.effective_message.reply_text(plain_text_table)
                update.effective_message.reply_text(part_temp_table, parse_mode=ParseMode.HTML)
        else:
            update.effective_message.reply_text("Error create table")
    else:
        update.effective_message.reply_text("Error get data from API.")


# Function to handle the /proposalall command
def proposal_all(update: Update, context: CallbackContext):
    try:
        api_url = 'https://it.api.namada.red/api/v1/chain/governance/proposals'
        response = requests.get(api_url)
        
        if response.status_code == 200:
            data = response.json()["proposals"]

            # Create PrettyTable
            table = create_table(data,"proposals")
            if table:
                # Split the table into batches
                count_rows = len(table._rows)
                batch_size = 25
                for start in range(0, count_rows, batch_size):
                    end = min(start + batch_size, count_rows)
                    temp_table = table.get_string(start=start, end=end)
                    part_temp_table = f'<pre>{temp_table}</pre>'
                    update.effective_message.reply_text(part_temp_table, parse_mode=ParseMode.HTML)
            else:
                update.effective_message.reply_text("Error create table")
        else:
            update.effective_message.reply_text("Error create table")
    except Exception as e:
        update.message.reply_text(f"Error: {e}")



# Function to handle the /proposalpending command
def proposal_pending(update: Update, context: CallbackContext):
    try:
        api_url = 'https://it.api.namada.red/api/v1/chain/governance/proposals'
        response = requests.get(api_url)
        
        if response.status_code == 200:
            data = response.json()["proposals"]
            table = create_table(data, "proposalpending")
            if table:
                # Split the table into batches
                count_rows = len(table._rows)
                batch_size = 25
                for start in range(0, count_rows, batch_size):
                    end = min(start + batch_size, count_rows)
                    temp_table = table.get_string(start=start, end=end)
                    part_temp_table = f'<pre>{temp_table}</pre>'
                    update.effective_message.reply_text(part_temp_table, parse_mode=ParseMode.HTML)
            else:
                update.effective_message.reply_text("Error create table")
        else:
            update.message.reply_text("Failed to fetch data from the API.")
    except Exception as e:
        update.message.reply_text(f"Error: {e}")

# Function to handle the /proposalpending command
def proposal_voting(update: Update, context: CallbackContext):
    try:
        api_url = 'https://it.api.namada.red/api/v1/chain/governance/proposals'
        response = requests.get(api_url)
        
        if response.status_code == 200:
            data = response.json()["proposals"]
            table = create_table(data, "votingproposals")
            if table:
                # Split the table into batches
                count_rows = len(table._rows)
                batch_size = 15
                for start in range(0, count_rows, batch_size):
                    end = min(start + batch_size, count_rows)
                    temp_table = table.get_string(start=start, end=end)
                    part_temp_table = f'<pre>{temp_table}</pre>'
                    update.effective_message.reply_text(part_temp_table, parse_mode=ParseMode.HTML)
            else:
                update.effective_message.reply_text("Error create table")
        else:
            update.message.reply_text("Failed to fetch data from the API.")
    except Exception as e:
        update.message.reply_text(f"Error: {e}")

def pgf(update: Update, context: CallbackContext) -> None:
    try:
       
        parameter_api_url = 'https://it.api.namada.red/api/v1/chain/parameter'
        parameter_response = requests.get(parameter_api_url)
        
        
        steward_api_url = 'https://it.api.namada.red/api/v1/chain/pgf/stewards'
        steward_response = requests.get(steward_api_url)
        
       
        if parameter_response.status_code == 200 and steward_response.status_code == 200:
            parameter_data = parameter_response.json()['parameters']
            stewards = steward_response.json()['stewards']              
            # Tạo tin nhắn text với thông tin từ hai nguồn
            message = f"Epoch: {parameter_data['epoch']}\n"
            message = f"Total PGF Stewards: {len(stewards)}\n"
            message += f"PGF Treasury: {parameter_data['pgf_treasury']}\n"
            message += f"PGF Inflation(%): {parameter_data['pgf_treasury_inflation']}%\n"
            message += f"Steward Incent/year (%): {parameter_data['pos_inflation']}%\n"         
            # Gửi tin nhắn
            update.effective_message.reply_text(message)
        else:
            update.effective_message.reply_text("Error get data from API.")
    except Exception as e:
        update.effective_message.reply_text(f"Lỗi: {e}")

def steward(update: Update, context: CallbackContext) -> None:
    try:
       # Get the list of stewards from the /api/v1/chain/pgf/stewards endpoint
        steward_api_url = 'https://it.api.namada.red/api/v1/chain/pgf/stewards'
        steward_response = requests.get(steward_api_url)
        
       # Check if the request was successful
        if steward_response.status_code == 200:
            stewards = steward_response.json()['stewards']
            
           # Create messages with stewards list
            message = f"List of Stewards | Total: {len(stewards)}\n"
            message += "\n".join(stewards)
            
            # Gửi tin nhắn
            update.effective_message.reply_text(message)
        else:
            update.effective_message.reply_text("Error get data")
    except Exception as e:
        update.effective_message.reply_text(f"Error: {e}")
        



def transaction(update: Update, context: CallbackContext) -> None:
    try:
        # Get the hash code from the user's message
        hash_value = context.args[0]
        
       # Generate URL to send request
        api_url = f'https://api-namada.cosmostation.io/tx/{hash_value}'
        
       # Send API request
        response = requests.get(api_url)
        
       # Check if the request was successful
        if response.status_code == 200:
            tx_data = response.json()
            
            # Tạo tin nhắn với dữ liệu giao dịch
            message = f"Hash: {tx_data['hash']}\n"
            message += f"Block ID: {tx_data['block_id']}\n"
            message += f"Transaction Type: {tx_data['tx_type']}\n"
            message += f"Wrapper ID: {tx_data['wrapper_id']}\n"
            message += f"Code: {tx_data['code']}\n"
            message += f"Data: {tx_data['data']}\n"
            
            # Check if specific transaction data is available
            if 'tx' in tx_data:
                message += "Transaction Details:\n"
                # Lặp qua từng loại giao dịch và thêm thông tin vào tin nhắn
                for tx_type, tx_details in tx_data['tx'].items():
                    message += f"\n{tx_type}:\n"
                    for key, value in tx_details.items():
                        message += f"{key}: {value}\n"
            
           # Send messages with transaction information
            update.effective_message.reply_text(message)
        else:
            update.effective_message.reply_text("Failed to fetch transaction data.")
    except IndexError:
        update.effective_message.reply_text("Please provide a transaction hash.")
    except Exception as e:
        update.effective_message.reply_text(f"Error: {e}")

# Define the function to handle the /searchcrew command
def search_player(update: Update, context: CallbackContext) -> None:
    # Get the user's message information
    memo = " ".join(context.args)
    
    # Check if the memo starts with "tpknam" or "tnam"
    if memo.startswith("tpknam") or memo.startswith("tnam"):
        # Send an API request to get data
        api_url = f"https://it.api.namada.red/api/v1/player/search/{memo}?player_kind=Crew"
        response = requests.get(api_url)
        
        # Handle the response from the API
        if response.status_code == 200:
            data = response.json()["players"]
            if data:
                
                player_info = data[0]  # Get the information of the first player in the list
                formatted_score = "{:,}".format(player_info['score'])
                message = f"Moniker: {player_info['moniker']}\n"
                message += f"Player Address: {player_info['player_address']}\n"
                message += f"Score: {formatted_score}\n"
                message += f"Ranking Position: {player_info['ranking_position']}\n"
                message += f"Avatar URL: {player_info['avatar_url']}\n"
                message += f"Is Banned: {player_info['is_banned']}\n"
                update.message.reply_text(message)
            else:
                update.message.reply_text("No information found for this memo.")
        else:
            update.message.reply_text("An error occurred while sending a request to the API.")
    else:
        update.message.reply_text("Invalid memo.")




def help_command(update: Update, context: CallbackContext) -> None:
    help_text = "THIS IS NAMADA.THE BEST BLOCKCHAIN THERE IS\n"
    help_text += "WE WILL DEFINITELY PROCESS ALL QUERIES,tpknam1qrxc7z4txljwl8dzwq5cucf7egp4td30s09lh2xdkl9qdqv8ktn4q63l84q\n"
    update.effective_message.reply_text(help_text)


def main() -> None:
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("info", info))
    dp.add_handler(CommandHandler("txn", transaction))
    dp.add_handler(CommandHandler("searchplayer", search_player))
    dp.add_handler(CommandHandler("proposals", proposal_all))
    dp.add_handler(CommandHandler("pendingproposals", proposal_pending))
    dp.add_handler(CommandHandler("votingproposals", proposal_voting))
    dp.add_handler(CommandHandler("topvalidator", topvalidators))
    dp.add_handler(CommandHandler("steward", steward))
    dp.add_handler(CommandHandler("pgf", pgf))
    dp.add_handler(CommandHandler("help", help_command))
    dp.add_handler(CommandHandler("start", help_command))
    updater.start_webhook(listen="0.0.0.0", port=PORT, url_path=TOKEN, webhook_url=APP_URL + TOKEN)
    updater.idle()

    return

if __name__ == '__main__':
    main()
