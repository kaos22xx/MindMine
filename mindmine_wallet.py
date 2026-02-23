#!/usr/bin/env python3
# MindMine Wallet v1.0
#!/usr/bin/env python3
# A simple desktop wallet for MIND token on Arbitrum

import tkinter as tk
from tkinter import ttk, messagebox
import json
from web3 import Web3
from eth_account import Account
import requests
from PIL import Image, ImageTk
import os
import base64
from cryptography.fernet import Fernet

# Generate a key: Fernet.generate_key()
# Keep this key safe - you'll need it to decrypt your wallet
ENCRYPTION_KEY = b'qXVpL20n7FTatp7oLK1Nhv80uLf5TZrLt36ECcwib2w='
fernet = Fernet(ENCRYPTION_KEY)

VERSION = "1.0"

# Configuration
RPC_URL = "https://arb1.arbitrum.io/rpc"
CONTRACT_ADDRESS = "0x6B3CAEBdD0c24dccc3eAe262d49092eEBAD773ed"
CONTRACT_ABI = [
    {"constant": True, "inputs": [], "name": "name", "outputs": [{"name": "", "type": "string"}], "type": "function"},
    {"constant": True, "inputs": [], "name": "symbol", "outputs": [{"name": "", "type": "string"}], "type": "function"},
    {"constant": True, "inputs": [], "name": "decimals", "outputs": [{"name": "", "type": "uint8"}], "type": "function"},
    {"constant": True, "inputs": [{"name": "owner", "type": "address"}], "name": "balanceOf", "outputs": [{"name": "", "type": "uint256"}], "type": "function"},
    {"constant": False, "inputs": [{"name": "to", "type": "address"}, {"name": "amount", "type": "uint256"}], "name": "transfer", "outputs": [{"name": "", "type": "bool"}], "type": "function"},
    {"constant": True, "inputs": [], "name": "totalSupply", "outputs": [{"name": "", "type": "uint256"}], "type": "function"},
    {"constant": True, "inputs": [], "name": "minedCount", "outputs": [{"name": "", "type": "uint256"}], "type": "function"},
]

class MindMineWallet:
    def __init__(self, root):
        self.root = root
        self.root.title("MindMine Wallet")
        self.root.geometry("500x700")
        self.root.resizable(False, False)
        
        # Web3 connection
        self.w3 = Web3(Web3.HTTPProvider(RPC_URL))
        self.contract = self.w3.eth.contract(
            address=CONTRACT_ADDRESS,
            abi=CONTRACT_ABI
        )
        
        # Load wallet data
        self.private_key = None
        self.address = None
        
        # UI
        self.setup_ui()
        self.load_wallet()
        
    def setup_ui(self):
        # Background
        self.root.configure(bg='#0a0a0f')
        
        # Header with logo
        header_frame = tk.Frame(self.root, bg='#1a1a2e', height=140)
        header_frame.pack(fill='x')
        header_frame.pack_propagate(False)
        
        # Try to load logo
        try:
            logo_path = os.path.join(os.path.dirname(__file__), 'mindmine_brain.png')
            if os.path.exists(logo_path):
                img = Image.open(logo_path)
                img = img.resize((80, 80), Image.Resampling.LANCZOS)
                self.logo = ImageTk.PhotoImage(img)
                logo_label = tk.Label(header_frame, image=self.logo, bg='#1a1a2e')
                logo_label.pack(pady=10)
        except:
            pass
        
        title_label = tk.Label(header_frame, text="MindMine Wallet", 
                              font=('Arial', 22, 'bold'), 
                              bg='#1a1a2e', fg='#00d4ff')
        title_label.pack(pady=5)
        
        # Wallet info frame
        info_frame = tk.Frame(self.root, bg='#0a0a0f')
        info_frame.pack(fill='x', padx=20, pady=20)
        
        # Address
        tk.Label(info_frame, text="Address:", bg='#0a0a0f', fg='#888').grid(row=0, column=0, sticky='w')
        self.address_label = tk.Label(info_frame, text="Not loaded", bg='#0a0a0f', fg='#00d4ff', font=('Courier', 9))
        self.address_label.grid(row=0, column=1, sticky='w', padx=10)
        
        # Balance
        tk.Label(info_frame, text="MIND Balance:", bg='#0a0a0f', fg='#888').grid(row=1, column=0, sticky='w', pady=10)
        self.balance_label = tk.Label(info_frame, text="0 MIND", bg='#0a0a0f', fg='#fff', font=('Arial', 14, 'bold'))
        self.balance_label.grid(row=1, column=1, sticky='w', padx=10)
        
        # ETH Balance
        tk.Label(info_frame, text="ETH Balance:", bg='#0a0a0f', fg='#888').grid(row=2, column=0, sticky='w')
        self.eth_balance_label = tk.Label(info_frame, text="0 ETH", bg='#0a0a0f', fg='#fff')
        self.eth_balance_label.grid(row=2, column=1, sticky='w', padx=10)
        
        # Mined blocks
        tk.Label(info_frame, text="Blocks Mined:", bg='#0a0a0f', fg='#888').grid(row=3, column=0, sticky='w', pady=10)
        self.mined_label = tk.Label(info_frame, text="0", bg='#0a0a0f', fg='#9b59b6')
        self.mined_label.grid(row=3, column=1, sticky='w', padx=10)
        
        # Buttons frame
        btn_frame = tk.Frame(self.root, bg='#0a0a0f')
        btn_frame.pack(fill='x', padx=20, pady=10)
        
        # Load Wallet button
        self.load_btn = tk.Button(btn_frame, text="Load Wallet", command=self.load_wallet_dialog,
                                  bg='#6b3cae', fg='#fff', font=('Arial', 11),
                                  relief='flat', padx=20, pady=8)
        self.load_btn.pack(fill='x', pady=5)
        
        # Transfer button
        self.transfer_btn = tk.Button(btn_frame, text="Transfer MIND", command=self.transfer_dialog,
                                      bg='#2ecc71', fg='#fff', font=('Arial', 11),
                                      relief='flat', padx=20, pady=8, state='disabled')
        self.transfer_btn.pack(fill='x', pady=5)
        
        # Refresh button
        refresh_btn = tk.Button(btn_frame, text="Refresh", command=self.refresh_balance,
                                bg='#34495e', fg='#fff', font=('Arial', 11),
                                relief='flat', padx=20, pady=8)
        refresh_btn.pack(fill='x', pady=5)
        
        # Network info
        net_frame = tk.Frame(self.root, bg='#0a0a0f')
        net_frame.pack(side='bottom', fill='x', padx=20, pady=10)
        
        tk.Label(net_frame, text="Network: Arbitrum One", bg='#0a0a0f', fg='#888', font=('Arial', 8)).pack()
        tk.Label(net_frame, text="Token: MIND (MindMine)", bg='#0a0a0f', fg='#888', font=('Arial', 8)).pack()
        tk.Label(net_frame, text="Version: " + VERSION, bg='#0a0a0f', fg='#666', font=('Arial', 7)).pack()
        
    def load_wallet(self):
        # Try to load saved wallet (encrypted)
        wallet_file = os.path.expanduser('~/.mindmine_wallet')
        if os.path.exists(wallet_file):
            try:
                with open(wallet_file, 'r') as f:
                    data = json.load(f)
                    encrypted_key = data.get('encrypted_key')
                    if encrypted_key:
                        # Decrypt the key
                        self.private_key = fernet.decrypt(encrypted_key.encode()).decode()
                        self.address = Account.from_key(self.private_key).address
                        self.address_label.config(text=self.address[:10] + '...' + self.address[-8:])
                        self.transfer_btn.config(state='normal')
                        self.refresh_balance()
            except Exception as e:
                print(f"Failed to load wallet: {e}")
                pass
                
    def load_wallet_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Load Wallet")
        dialog.geometry("400x200")
        dialog.configure(bg='#1a1a2e')
        
        tk.Label(dialog, text="Enter Private Key:", bg='#1a1a2e', fg='#fff').pack(pady=10)
        
        key_entry = tk.Entry(dialog, width=50, show='*')
        key_entry.pack(pady=10)
        
        def save_wallet():
            key = key_entry.get().strip()
            if key.startswith('0x'):
                key = key[2:]
            try:
                account = Account.from_key(key)
                self.private_key = key
                self.address = account.address
                
                # Save wallet (encrypted)
                wallet_file = os.path.expanduser('~/.mindmine_wallet')
                encrypted = fernet.encrypt(key.encode()).decode()
                with open(wallet_file, 'w') as f:
                    json.dump({'encrypted_key': encrypted}, f)
                
                self.address_label.config(text=self.address[:10] + '...' + self.address[-8:])
                self.transfer_btn.config(state='normal')
                self.refresh_balance()
                dialog.destroy()
                messagebox.showinfo("Success", "Wallet loaded successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Invalid private key: {str(e)}")
        
        tk.Button(dialog, text="Load", command=save_wallet, bg='#6b3cae', fg='#fff').pack(pady=10)
        
    def refresh_balance(self):
        if not self.address:
            return
            
        try:
            # Get MIND balance
            balance = self.contract.functions.balanceOf(self.address).call()
            decimals = self.contract.functions.decimals().call()
            mind_balance = balance / (10 ** decimals)
            self.balance_label.config(text=f"{mind_balance:,.2f} MIND")
            
            # Get ETH balance
            eth_balance = self.w3.eth.get_balance(self.address)
            self.eth_balance_label.config(text=f"{eth_balance / 1e18:.6f} ETH")
            
            # Get mined count
            mined = self.contract.functions.minedCount().call()
            self.mined_label.config(text=str(mined))
            
        except Exception as e:
            print(f"Error refreshing: {e}")
            
    def transfer_dialog(self):
        if not self.address:
            messagebox.showwarning("Warning", "Please load wallet first")
            return
            
        dialog = tk.Toplevel(self.root)
        dialog.title("Transfer MIND")
        dialog.geometry("400x250")
        dialog.configure(bg='#1a1a2e')
        
        tk.Label(dialog, text="Recipient Address:", bg='#1a1a2e', fg='#fff').pack(pady=5)
        to_entry = tk.Entry(dialog, width=45)
        to_entry.pack(pady=5)
        
        tk.Label(dialog, text="Amount (MIND):", bg='#1a1a2e', fg='#fff').pack(pady=5)
        amount_entry = tk.Entry(dialog, width=20)
        amount_entry.pack(pady=5)
        
        def do_transfer():
            to_address = to_entry.get().strip()
            amount_str = amount_entry.get().strip()
            
            if not to_address or not amount_str:
                messagebox.showerror("Error", "Please fill all fields")
                return
                
            try:
                decimals = self.contract.functions.decimals().call()
                amount = int(float(amount_str) * (10 ** decimals))
                
                # Build transaction
                nonce = self.w3.eth.get_transaction_count(self.address)
                gas_price = self.w3.eth.gas_price
                
                tx = self.contract.functions.transfer(to_address, amount).build_transaction({
                    'from': self.address,
                    'nonce': nonce,
                    'gasPrice': gas_price,
                    'chainId': 42161
                })
                
                # Estimate gas
                gas_estimate = self.w3.eth.estimate_gas(tx)
                tx['gas'] = gas_estimate
                
                # Sign and send
                signed_tx = self.w3.eth.account.sign_transaction(tx, self.private_key)
                tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
                
                messagebox.showinfo("Success", f"Transaction sent!\nHash: {tx_hash.hex()}")
                dialog.destroy()
                self.refresh_balance()
                
            except Exception as e:
                messagebox.showerror("Error", f"Transfer failed: {str(e)}")
        
        tk.Button(dialog, text="Send", command=do_transfer, bg='#2ecc71', fg='#fff', 
                 font=('Arial', 11, 'bold')).pack(pady=20)

def main():
    root = tk.Tk()
    app = MindMineWallet(root)
    root.mainloop()

if __name__ == "__main__":
    import sys
    try:
        main()
    except Exception as e:
        print(f"Error: {e}")
        input("Press Enter to exit...")
