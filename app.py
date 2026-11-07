import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# Настройки страницы
st.set_page_config(
    page_title='Анализ интернет-магазина',
    page_icon='📊',
    layout='wide'
)

# Немного оформления
st.markdown("""
<style>
.stApp {
    background-color: #101820;
}
h1 {
    color: #F1F5F9;
}
h2, h3 {
    color: #E2E8F0;
}
div[data-testid="stMetric"] {
    background-color: #1B2836;
    border: 1px solid #29394A;
    padding: 18px;
    border-radius: 10px;
}
div[data-testid="stMetricLabel"] {
    color: #94A3B8;
}
div[data-testid="stMetricValue"] {
    color: #00D1B2;
}
</style>
""", unsafe_allow_html=True)

# Цвета для графиков
MAIN_COLOR = '#00D1B2'
SECOND_COLOR = '#3B82F6'
BG_COLOR = '#1B2836'
TEXT_COLOR = '#E2E8F0'
GRID_COLOR = '#334155'


# Функция для оформления графиков
def style_chart(ax, title, xlabel='', ylabel=''):
    ax.set_facecolor(BG_COLOR)
    ax.set_title(title, color=TEXT_COLOR, fontsize=13, loc='left', pad=15)
    ax.set_xlabel(xlabel, color=TEXT_COLOR)
    ax.set_ylabel(ylabel, color=TEXT_COLOR)
    ax.tick_params(colors=TEXT_COLOR)

    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.spines['bottom'].set_color(GRID_COLOR)

    ax.grid(axis='x', color=GRID_COLOR, linestyle='--', alpha=0.5)
    ax.set_axisbelow(True)


# Загрузка таблиц
@st.cache_data
def load_data():
    orders = pd.read_csv('data/orders.csv')
    users = pd.read_csv('data/users.csv')
    items = pd.read_csv('data/items.csv')
    return orders, users, items


orders, users, items = load_data()

st.title('Анализ заказов интернет-магазина')


# Объединяем таблицы
df = orders.merge(users, on='user_id', how='left')
df = df.merge(items, on='item_id', how='left')

# Приводим столбцы к нужным типам
df['order_date'] = pd.to_datetime(df['order_date'], errors='coerce')
df['quantity'] = pd.to_numeric(df['quantity'], errors='coerce')
df['price_per_unit'] = pd.to_numeric(df['price_per_unit'], errors='coerce')

# Считаем выручку
df['revenue'] = df['quantity'] * df['price_per_unit']


# Проверяем данные до очистки
st.subheader('Объединённые данные')
st.dataframe(df.head(10), use_container_width=True)
st.write('Размер таблицы:', df.shape)

st.subheader('Проверка пропусков')
st.write('Пропуски до очистки:')
st.dataframe(df.isnull().sum())

# Убираем строки, в которых нет важных данных
df = df.dropna(subset=[
    'order_id', 'user_id', 'item_id', 'order_date',
    'quantity', 'price_per_unit'
])

# В некоторых строках могут отсутствовать названия или категории
df['category'] = df['category'].fillna('Не указана')
df['item_name'] = df['item_name'].fillna('Не указан')
df['user_segment'] = df['user_segment'].fillna('Не указан')

# После очистки считаем выручку ещё раз
df['revenue'] = df['quantity'] * df['price_per_unit']

st.write('Размер таблицы после очистки:', df.shape)
st.write('Пропуски после очистки:')
st.dataframe(df.isnull().sum())
st.write('Всего пропусков:', int(df.isnull().sum().sum()))


# Фильтры и таблица
st.subheader('Данные')

if not df.empty:
    categories = ['Все'] + sorted(df['category'].unique().tolist())

    selected_category = st.selectbox(
        'Категория товара',
        categories
    )

    min_date = df['order_date'].min().date()
    max_date = df['order_date'].max().date()

    date_range = st.date_input(
        'Период',
        value=(min_date, max_date)
    )

    filtered_df = df.copy()

    if selected_category != 'Все':
        filtered_df = filtered_df[
            filtered_df['category'] == selected_category
        ]

    # Фильтр работает и когда выбрана одна дата, и когда выбран период
    if isinstance(date_range, (tuple, list)):
        if len(date_range) == 2:
            start_date, end_date = date_range
            filtered_df = filtered_df[
                (filtered_df['order_date'].dt.date >= start_date) &
                (filtered_df['order_date'].dt.date <= end_date)
            ]
    else:
        filtered_df = filtered_df[
            filtered_df['order_date'].dt.date == date_range
        ]

    st.dataframe(filtered_df, use_container_width=True)
    st.write('Количество строк:', len(filtered_df))

else:
    filtered_df = df.copy()
    st.write('В таблице нет данных после очистки.')


# Основные показатели
st.subheader('Основные показатели')

total_orders = filtered_df['order_id'].nunique()
total_revenue = filtered_df['revenue'].sum()
unique_users = filtered_df['user_id'].nunique()

if total_orders > 0:
    average_check = total_revenue / total_orders
else:
    average_check = 0

col1, col2, col3, col4 = st.columns(4)

col1.metric('Заказы', f'{total_orders:,}')
col2.metric('Выручка', f'{total_revenue:,.2f} ₽')
col3.metric('Клиенты', f'{unique_users:,}')
col4.metric('Средний чек', f'{average_check:,.2f} ₽')


# Графики и выводы
if not filtered_df.empty:

    st.subheader('Графики')

    # Топ товаров по выручке
    top_products = (
        filtered_df.groupby('item_name')['revenue']
        .sum()
        .sort_values(ascending=False)
        .head(10)
        .sort_values()
    )

    fig, ax = plt.subplots(figsize=(11, 5))
    fig.patch.set_facecolor(BG_COLOR)

    bars = ax.barh(
        top_products.index,
        top_products.values,
        color=MAIN_COLOR
    )

    ax.bar_label(bars, fmt='{:,.0f} ₽', color=TEXT_COLOR, padding=5)
    style_chart(ax, 'Топ товаров по выручке', 'Выручка, руб.')
    plt.tight_layout()
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)

    # Выручка по категориям
    category_revenue = (
        filtered_df.groupby('category')['revenue']
        .sum()
        .sort_values()
    )

    fig, ax = plt.subplots(figsize=(10, 4))
    fig.patch.set_facecolor(BG_COLOR)

    bars = ax.barh(
        category_revenue.index,
        category_revenue.values,
        color=SECOND_COLOR
    )

    ax.bar_label(bars, fmt='{:,.0f} ₽', color=TEXT_COLOR, padding=5)
    style_chart(ax, 'Выручка по категориям', 'Выручка, руб.')
    plt.tight_layout()
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)

    # Количество заказов по дням недели
    weekday_names = [
        'Понедельник', 'Вторник', 'Среда', 'Четверг',
        'Пятница', 'Суббота', 'Воскресенье'
    ]

    weekday_orders = (
        filtered_df.assign(
            weekday=filtered_df['order_date'].dt.dayofweek
        )
        .groupby('weekday')['order_id']
        .nunique()
        .reindex(range(7), fill_value=0)
    )

    max_day = weekday_orders.idxmax()

    colors = [
        MAIN_COLOR if day == max_day else SECOND_COLOR
        for day in weekday_orders.index
    ]

    fig, ax = plt.subplots(figsize=(11, 5))
    fig.patch.set_facecolor(BG_COLOR)

    bars = ax.bar(
        weekday_names,
        weekday_orders.values,
        color=colors,
        width=0.6
    )

    ax.bar_label(bars, color=TEXT_COLOR, padding=5)
    ax.set_facecolor(BG_COLOR)
    ax.set_title(
        'Заказы по дням недели',
        color=TEXT_COLOR,
        fontsize=13,
        loc='left',
        pad=15
    )
    ax.set_ylabel('Количество заказов', color=TEXT_COLOR)
    ax.tick_params(colors=TEXT_COLOR)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.spines['bottom'].set_color(GRID_COLOR)
    ax.grid(axis='y', color=GRID_COLOR, linestyle='--', alpha=0.5)
    ax.set_axisbelow(True)

    plt.xticks(rotation=20)
    plt.tight_layout()
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)


    # Небольшие выводы по данным
    st.subheader('Что получилось')

    top_category = category_revenue.idxmax()
    top_category_revenue = category_revenue.max()

    top_product = top_products.idxmax()
    top_product_revenue = top_products.max()

    best_weekday = weekday_names[max_day]
    best_weekday_count = weekday_orders.max()

    st.write(
        f'Больше всего выручки принесла категория {top_category} '
        f'— {top_category_revenue:,.2f} ₽.'
    )

    st.write(
        f'Самый доходный товар — {top_product}. '
        f'Выручка по нему составила {top_product_revenue:,.2f} ₽.'
    )

    st.write(
        f'Больше всего заказов было в день: {best_weekday}. '
        f'Количество заказов — {best_weekday_count}.'
    )

    st.write(f'Средний чек составил {average_check:,.2f} ₽.')

else:
    st.write('По выбранным фильтрам ничего не нашлось.')
