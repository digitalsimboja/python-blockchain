# A simple blockchain implementation using Python

## Instructions to run
Clone the project

```
https://github.com/digitalsimboja/python-blockchain.git

```

Install the requirements
```
cd python-blockchain
pip install -r requirements.txt

```
## Test with Fastapi
Run the app on the terminal:
```
uvicorn blockchain_app.main:app --reload
```
This Generates Keypair and saves it on the local storage

The endpoints can be tested on the Fastapi Swagger UI by visiting
```
127.0.0.1:8000/docs#/default/
```

Use the sample data below to generate list of at least 10 transactions
```
{
   "data":"Buy me a coffee",
   "pub_key":"[90155580029687883164432592187174752467492490098477989544923434207160016494724, 13458123714560040485211368563377546414457054996102504146220313984076916101699]",
   "signature":"[49352579840778331840587226980074533148813020209416002427540746677125201223893, 61794404799422710702980425188102977369003292361923370115807578184059711941988]",
   "transaction_id":"e1a29a279de1gjddgkkgkgh5bce8761b"
}
```



