## Similar Wallet

This project is used to find similar wallets based on the [Annoy Index]([Title](https://github.com/spotify/annoy)).

### How to use

1. Install the requirements

```shell
poetry install
```

2. Create sample data via Annoy Index

- similar_wallets.ann – Annoy Index file length of item vector that will be indexed = 5 and metric="euclidean". For example:
  - wallet_index – Wallet index
  - balance – Wallet balance
  - overall_transaction_count – Wallet transaction count
  - last_month_transaction_count – Wallet transaction count in last month
  - nft_count – Wallet nft count
  - rank – Wallet rank
- map.csv – Map file with wallet_index and wallet_name


3. Run the script

```shell
poetry run python app/main.py
```

4. Test the script

```shell
# {address} is the wallet address. For example – 0xbab41d6486f8fd63d2ca790818a11756b0579894
# {n} is the number of similar wallets. For example – 3
curl -X GET http://127.0.0.1:8000/annoy/{address}?n={n}
```