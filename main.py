import os
import sqlite3
import pandas as pd


def main():
    os.makedirs('output', exist_ok=True)

    input_db = os.path.join('data', 'shop.sqlite')
    output_db = os.path.join('output', 'shop_analysis.sqlite')

    if not os.path.exists(input_db):
        print(f"Помилка: Файл {input_db} не знайдено! Перевірте його наявність у папці data.")
        return

    print("Зчитування даних з початкової бази...")
    conn_in = sqlite3.connect(input_db)
    df_products = pd.read_sql_query("SELECT * FROM products", conn_in)
    df_sales = pd.read_sql_query("SELECT * FROM sales", conn_in)
    conn_in.close()

    df_merged = pd.merge(df_sales, df_products, left_on='product_id', right_on='id', suffixes=('_sale', '_prod'))
    df_merged['sale_amount'] = df_merged['quantity'] * df_merged['price']

    print("Розрахунок статистики по товарах...")
    product_statistics = df_merged.groupby(['product_id', 'name', 'category']).agg(
        quantity_sold=('quantity', 'sum'),
        total_sales=('sale_amount', 'sum')
    ).reset_index().drop(columns=['product_id'])
    product_statistics = product_statistics[['name', 'category', 'quantity_sold', 'total_sales']]

    print("Розрахунок статистики по категоріях...")
    category_statistics = df_merged.groupby('category').agg(
        sales_ops_count=('id_sale', 'count'),
        units_sold=('quantity', 'sum'),
        total_revenue=('sale_amount', 'sum'),
        avg_sale_amount=('sale_amount', 'mean')
    ).reset_index()

    print("Визначення Топ-5 найпопулярніших товарів...")
    top_products = product_statistics.sort_values(by='quantity_sold', ascending=False).head(5)
    top_products = top_products.reset_index(drop=True)

    print(f"Запис таблиць у базу {output_db}...")
    conn_out = sqlite3.connect(output_db)

    product_statistics.to_sql('product_statistics', conn_out, if_exists='replace', index=False)
    category_statistics.to_sql('category_statistics', conn_out, if_exists='replace', index=False)
    top_products.to_sql('top_products', conn_out, if_exists='replace', index=False)

    conn_out.close()
    print("Аналіз успішно завершено! Нова база даних створена.")


if __name__ == '__main__':
    main()