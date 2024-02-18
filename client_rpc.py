import odoorpc
import configparser
import os
import csv
import urllib.request
import subprocess
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
# Obtenez le chemin du répertoire du script
script_directory = os.path.dirname(os.path.realpath(__file__))

# Construisez le chemin complet du fichier config.json
config_file_path = os.path.join(script_directory, 'service.conf')

# Check if the file exists before attempting to read it
if os.path.exists(config_file_path):
    config = configparser.ConfigParser()
    config_file = config.read(config_file_path)

    # Print the result of reading the configuration file
    print(f"Config file read successfully: {config_file}")
    
    # Now you can access configuration values like this:
    host = config.get('DEFAULT', 'HOST', fallback='')
    port = config.get('DEFAULT', 'PORT', fallback='')
    protocol = config.get('DEFAULT', 'PROTOCOL', fallback='')
    user = config.get('DEFAULT', 'USER', fallback='')
    db = config.get('DEFAULT', 'DB', fallback='')
    key = config.get('DEFAULT', 'KEY', fallback='')
    netauto = config.get('DEFAULT', 'NETAUTO', fallback='')

    # Print the extracted values
    print(f"Host: {host}")
    print(f"Port: {port}")
    print(f"Protocol: {protocol}")
    print(f"User: {user}")
    print(f"DB: {db}")
    print(f"NETAUTO: {netauto}")

else:
    print(f"The config file {config_file_path} is not found.")
# Vérifier si tous les paramètres nécessaires sont présents
if not all([host, port, protocol, user, db, key]):
    print("Please try to provide all the necessary parameters in the config file !")
else:
    # Tester la connexion avant d'initialiser odoorpc
    odoo_url = f"{protocol}://{host}:{port}"
    try:
        urllib.request.urlopen(odoo_url, timeout=10)
    except urllib.error.URLError as e:
        logger.error(f"Unable to connect to {odoo_url}: {e}")
        exit()

    # Préparer la connexion au serveur Odoo
    try:
        odoo = odoorpc.ODOO(host, port=int(port))
        # Afficher les bases de données disponibles
        print(host, port, user, db, key)
        # Se connecter à la base de données
        odoo.login(db, user, key)
        # Vérifier si le modèle product.template existe
        if 'product.template' in odoo.env:
            ProductTemplate = odoo.env['product.template']

            # Rechercher tous les produits
            product_ids = ProductTemplate.search([('to_weight', '=', True)])
            
            # Fetch product names and barcodes in a single loop
            product_data = [('1',product.default_code,product.pos_categ_id,product.list_price,'0',product.name, product.barcode) for product in ProductTemplate.browse(product_ids)]

            # Écrire les noms des produits dans un fichier CSV
            csv_file_path = os.path.join(script_directory, 'plu.csv')

            with open(csv_file_path, 'w', newline='', encoding='utf-8') as csv_file:
                csv_writer = csv.writer(csv_file, delimiter=';')
                csv_writer.writerow(['@UPDATE plu;;;;;;'])
                csv_writer.writerow(['1;0;1;0;0;Divers;2000000;0'])
                csv_writer.writerows(product_data)

            print(f"The product list have been written in {csv_file_path}")

            result_csv = subprocess.run([netauto, "csv", csv_file_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
            print("CSV Command Output:", result_csv.stdout.decode())
            print("CSV Command Error:", result_csv.stderr.decode())

            result_plu = subprocess.run([netauto, "plu"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
            print("PLU Command Output:", result_plu.stdout.decode())
            print("PLU Command Error:", result_plu.stderr.decode())

        else:
            print("The model 'product.template' is not found in Odoo.")

    except Exception as e:

        print(f"An error occurred during the connection to Odoo : {e}")
