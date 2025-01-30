import pandas as pd
import chardet
from django.core.exceptions import ValidationError
from Webshop.models import Item, ItemDetails, ItemCategory


def validate_product_data(df):
    errors = []

    for index, row in df.iterrows():
        try:
            item_name = str(row.get('item_name', '')).strip()
            item_description = str(row.get('item_description', '')).strip()
            category_name = str(row.get('item_category', '')).strip()
            item_price = str(row.get('item_price', '')).strip()
            item_stock = str(row.get('item_stock', '')).strip()
            article_id = str(row.get('article_id', '')).strip()

            if not item_name or not item_description or not category_name:
                errors.append(f"Zeile {index + 1}: Name, Beschreibung und Kategorie fehlen.")

            try:
                item_price = float(item_price.replace(",", ".")) if item_price else 0.0
                if item_price <= 0:
                    errors.append(f"Zeile {index + 1}: Der Preis muss eine Zahl größer als 0 sein.")
            except ValueError:
                errors.append(f"Zeile {index + 1}: Der Preis ist ungültig.")

            if not item_stock.isdigit():
                errors.append(f"Zeile {index + 1}: Der Lagerbestand muss eine gültige Zahl sein.")

            if len(article_id) < 4:
                errors.append(f"Zeile {index + 1}: Die Artikel-ID muss mindestens 4 Zeichen lang sein.")

        except Exception as e:
            errors.append(f"Zeile {index + 1}: Fehler beim Validieren - {e}")

    return errors


def process_product_upload(file):
    try:
        # Detect encoding
        raw_data = file.read()
        encoding_detected = chardet.detect(raw_data)['encoding']

        # Set default encoding to UTF-8
        if encoding_detected is None:
            encoding_detected = "UTF-8"

        print(f"Erkannte Kodierung: {encoding_detected}")

        # Reset file pointer
        file.seek(0)

        df = pd.read_csv(file, dtype=str, sep=";", keep_default_na=False, encoding=encoding_detected, quotechar='"')
        df.columns = df.columns.str.strip().str.lower()
        expected_columns = {'article_id', 'item_name', 'item_category', 'item_price', 'item_description', 'item_stock'}

        if not expected_columns.issubset(set(df.columns)):
            fehlende_spalten = expected_columns - set(df.columns)
            print(f"Fehlende Spalten in der Datei: {fehlende_spalten}")
            return

        validation_errors = validate_product_data(df)
        if validation_errors:
            raise ValidationError("\n".join(validation_errors))

        for index, row in df.iterrows():
            try:
                item_name = str(row['item_name']).strip()
                item_description = str(row['item_description']).strip()
                category_name = str(row['item_category']).strip()
                article_id = str(row['article_id']).strip()

                existing_item = Item.objects.filter(article_id=article_id).first()
                existing_price = existing_item.item_price if existing_item else 0.0
                existing_stock = existing_item.item_stock if existing_item else 0

                try:
                    new_price = float(row['item_price'].replace(",", ".")) if row['item_price'] else existing_price
                except ValueError:
                    new_price = existing_price

                updated_price = new_price
                try:
                    added_stock = int(float(row['item_stock'])) if row['item_stock'].isdigit() else 0
                except ValueError:
                    added_stock = 0

                new_stock = existing_stock + added_stock

                if not item_name or not category_name:
                    print(f"Zeile {index + 1}: Fehlende Werte! {row}")
                    continue

                category, created = ItemCategory.objects.get_or_create(category_name=category_name)
                if created:
                    print(f"Neue Kategorie '{category_name}' wurde angelegt.")

                item_details, _ = ItemDetails.objects.get_or_create(
                    item_name=item_name,
                    defaults={'item_description': item_description}
                )

                item, _ = Item.objects.update_or_create(
                    article_id=article_id,
                    defaults={
                        "item_price": updated_price,  # actualized price
                        "item_stock": new_stock,  # actualized stock
                        "item_details": item_details,
                    }
                )

                item_details.categories.add(category)

                print(f"Produkt '{item_details.item_name}' erfolgreich hinzugefügt!")

            except Exception as e:
                print(f"Fehler in Zeile {index + 1}: {e}")

    except ValidationError as e:
        print(f"Validierungsfehler: {e}")
    except UnicodeDecodeError:
        print("Fehler beim Dekodieren der Datei. Stelle sicher, dass die Datei UTF-8 oder ISO-8859-1 kodiert ist.")
    except pd.errors.ParserError as e:
        print(f"Fehler beim Einlesen der CSV: {e}")
    except Exception as e:
        print(f"Unerwarteter Fehler: {e}")