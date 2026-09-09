# My Shitty Finance Calculator

This is a finance calculator for budget tracking.

## Features

The calculator can keep transaction records, whose parties, the value of the mutations,
admin fees, and three important features:
- Sender: This does not describe the party, but this describes the institution (e.g. bank or e-money) that the sender uses.
- Receiver: Same with sender. This describes the institution that the receiver uses to obtain the money.
- Wallet: The "space" where transaction is conducted. This is useful if you want to seperate your funds into seperate wallet.
- Category: The type of transactions, e.g. food, school fees, taxes, etc.

Config is stored in ```./config.toml```, while database's default path is ```./database.db```. Use:

```bash
python3 run.py
```

To run the program, make sure ```sql``` and ```finance_mgr``` folder exist.

## Usages

Here are the commands:
- ```setup```    : Setup the entire project (config and/or database). Use ```--db``` and ```--archive``` flag to pass the database name and archive database name to the config respectively.
- ```database``` : Reset or obtain data from the database. Use ```database reset``` to reset, and ```database show``` to obtain data.
- ```sheet```    : Use this to import (```sheet import```) or export (```sheet export```) to spreadsheets (the only way to mutate data).
- ```graph```    : Display it within a graph. Use ```graph time``` to plot it against time (line graph), and ```graph [party, category, active, passive, wallet]``` to ploit against those classifications (bar chart). Use ```--noadmin``` to not include admin fees and ```--adminfee``` to show seperate graph of admin fees. If both flags are used you get a seperated graph of nominal value and admin fee.
- ```control```  : Use this for budget control. This requires config key ```limit``` (that sets transaction limit per day) and ```save``` (percentage of the transaction limit you wish to save into a seperate bucket). You can execute ```control show``` to show tables of each day or ```control graph``` that shows a plot of data in respect to time. So what is the data? It includes exceed (```show``` only, it shows whether you have exceeded or not), delta (actual delta between the total spending and limit), and saved (the saved cash).
- ```version```  : Use this to display version number. Use ```version --license``` to show what license.

There are several flags you can use when executing ```database show```, ```control```, ```graph```, and ```sheet export```. First, here are time flags.
- ```--date``` : Use this flag when obtaining data to filter based on dates with format ```YYYY-MM-DD:yyyy-mm-dd``` (start and end range), use comma for multiple ranges (e.g. ```YYYY-MM-DD:yyyy-mm-dd,YYYY-MM-DD:yyyy-mm-dd,YYYY-MM-DD:yyyy-mm-dd```)
- ```--yearmonth``` : Use this flag when obtaining data to filter based on dates, but this time with format ````YYYY-MM```
- ```--monthday```  : Use this flag when obtaining data to filter based on dates, but this time with format ```MM-DD```
- ```--year```      : Use this flag when obtaining data to filter based on dates, but this time with format ```YYYY```
- ```--month```     : Use this flag when obtaining data to filter based on dates, but this time with format ```MM```
- ```--day```       : Use this flag when obtaining data to filter based on dates, but this time with format ```DD```

Here are value flags. All of them use the format of either ```x=number``` (for equivalence statements) or ```number[operator]x[operator]number``` or ```number[operator]x``` or ```x[operator]number``` (for non-equivalence statements, e.g. ```100<x<200```, you can use ```<```, ```>```, ```<=```, and ```>=```). You can use multiple ranges e.g. ```x=100,500<x<600,x>800```
- ```--id```        : Use this flags when obtaining fata to filter based on IDs, which are incremental discrete integers.
- ```--nvalue```    : Use this flag when obtaining data to filter based on nominal transaction values.
- ```--tvalue```    : Use this flag when obtaining data to filter based on total transaction values (nominal + admin fee)
- ```--admin```     : Use this flag when obtaining data to filter based on admin fees.

Here are other flags. All of them are used to compare against active, passive wallet, party, pathway, and categories. Use comma to compare against multiple items e.g. ```apple,orange,grape```. All of the string must not contain whitespaces.
- ```--category```  : Use this for categories.
- ```--party```     : Use this for parties.
- ```--wallet```    : Use this for wallets.
- ```--pathway```   : Use this for pathways.
- ```--active```    : Use this for active side.
- ```--passive```   : Use this for the passive side.

There are several useful flags:
- ```--verbose``` for ```database show```, ```graph```, ```control```, and ```sheet export```, the SQL command will be displayed before you confirm.
- ```--overwrite``` for ```sheet import```, the data will overwrite instead of be appended.
- ```--nobackup``` for ```setup```, ```sheet import```, and ```database reset```, backup database will not be created.
- ```--summary``` for ```database show``` and ```control``` to generate only the summary (table is not generated).
- ```--show``` for ```control graph``` to show what graphs can be shown (either total, delta, or saved. use commas for seperation, do not use space. You can pick two items or more)

Notes:
- The spreadsheet file must contain sheet tab named 'Mutation'.
- The sheet must contain 'Date', 'Value', 'Admin', 'Total', 'Party', 'Category', 'Active', 'Passive', 'Pathway', and 'Wallet'.
- The database must contain table named 'transactions' with the same exact headers, but all must be lower case.
- The configuration file must be named 'config.toml' and placed directly at the root directory of the project.
- Pandas, tomlkit, and tabulate are required. Best to use the latest version of Python and all of the dependencies.
