default_questions = [
  {
    "question": """
      "What was our "
      "total sales, "
      "total margin ,"
      "percentage margin, "
      "total transactions, "
      "average order value and "
      "items per transaction "
      "for the fortnight that ends on {DATE}",
    """,
    "query" : """
        SELECT
            COALESCE(SUM(sales_amount), 0) AS total_sales,
            COALESCE(SUM(revenue), 0) AS total_margin,
            SAFE_DIVIDE(COALESCE(SUM(revenue), 0), NULLIF(SUM(sales_amount), 0)) * 100 AS percentage_margin,
            COUNT(DISTINCT ticket_id) AS total_transactions,
            SAFE_DIVIDE(COALESCE(SUM(sales_amount), 0), NULLIF(COUNT(DISTINCT ticket_id), 0)) AS average_order_value,
            SAFE_DIVIDE(COALESCE(SUM(quantity), 0), NULLIF(COUNT(DISTINCT ticket_id), 0)) AS items_per_transaction
        FROM fact_sales
        WHERE DATE(created_at) BETWEEN DATE_SUB('{DATE}', INTERVAL 14 DAY) AND '{DATE}'
    """
  },
  {
    "question":
      "What is the difference in $ and % variation between "
      "total sales, "
      "total margin,"
      "percentage margin, "
      "total transactions, "
      "average order value and "
      "items per transaction, "
      "comparing the fortnight that ends on {DATE} versus the fortnight from {n_weeks} week(s) ago, "
      "for comparable, new, and total stores."
      "New stores are considered to be those less than 1 year old and comparable stores are those that are 1 year old or more.",
    "query": """
        WITH store_classification AS 
        (
          SELECT
              store_id,
              CASE
                  WHEN MIN(DATE(created_at)) <= DATE_SUB('{DATE}', INTERVAL 1 YEAR) THEN 'comparable'
                  ELSE 'new'
              END AS store_type
          FROM fact_sales
          GROUP BY store_id
        ),
        current_fortnight AS 
        (
          SELECT
            store_classification.store_type,
            SUM(sales_amount) AS sales,
            SUM(revenue) AS margin,
            SAFE_DIVIDE(SUM(revenue), NULLIF(SUM(sales_amount), 0)) AS percentage_margin,
            COUNT(DISTINCT ticket_id) AS transactions,
            SAFE_DIVIDE(SUM(sales_amount), NULLIF(COUNT(DISTINCT ticket_id), 0)) AS average_order_value,
            SAFE_DIVIDE(SUM(quantity), NULLIF(COUNT(DISTINCT ticket_id), 0)) AS items_per_transaction
          FROM fact_sales
          JOIN store_classification ON fact_sales.store_id = store_classification.store_id
          WHERE DATE(created_at) BETWEEN DATE_SUB('{DATE}', INTERVAL 14 DAY) AND '{DATE}'
          GROUP BY store_classification.store_type
          UNION ALL
          SELECT
            'total' AS store_type,
            SUM(sales_amount) AS sales,
            SUM(revenue) AS margin,
            SAFE_DIVIDE(SUM(revenue), NULLIF(SUM(sales_amount), 0)) AS percentage_margin,
            COUNT(DISTINCT ticket_id) AS transactions,
            SAFE_DIVIDE(SUM(sales_amount), NULLIF(COUNT(DISTINCT ticket_id), 0)) AS average_order_value,
            SAFE_DIVIDE(SUM(quantity), NULLIF(COUNT(DISTINCT ticket_id), 0)) AS items_per_transaction
          FROM fact_sales
          WHERE DATE(created_at) BETWEEN DATE_SUB('{DATE}', INTERVAL 14 DAY) AND '{DATE}'
        ),
        previous_period_same_fortnight AS 
        (
          SELECT
            store_classification.store_type,
            SUM(sales_amount) AS sales,
            SUM(revenue) AS margin,
            SAFE_DIVIDE(SUM(revenue), NULLIF(SUM(sales_amount), 0)) AS percentage_margin,
            COUNT(DISTINCT ticket_id) AS transactions,
            SAFE_DIVIDE(SUM(sales_amount), NULLIF(COUNT(DISTINCT ticket_id), 0)) AS average_order_value,
            SAFE_DIVIDE(SUM(quantity), NULLIF(COUNT(DISTINCT ticket_id), 0)) AS items_per_transaction
          FROM fact_sales
          JOIN store_classification ON fact_sales.store_id = store_classification.store_id
          WHERE DATE(created_at) BETWEEN DATE_SUB(DATE_SUB('{DATE}', INTERVAL 14 DAY), INTERVAL {n_weeks} WEEK) AND DATE_SUB('{DATE}', INTERVAL {n_weeks} WEEK)
          GROUP BY store_classification.store_type
          UNION ALL
          SELECT
            'total' AS store_type,
            SUM(sales_amount) AS sales,
            SUM(revenue) AS margin,
            SAFE_DIVIDE(SUM(revenue), NULLIF(SUM(sales_amount), 0)) AS percentage_margin,
            COUNT(DISTINCT ticket_id) AS transactions,
            SAFE_DIVIDE(SUM(sales_amount), NULLIF(COUNT(DISTINCT ticket_id), 0)) AS average_order_value,
            SAFE_DIVIDE(SUM(quantity), NULLIF(COUNT(DISTINCT ticket_id), 0)) AS items_per_transaction
          FROM fact_sales
          WHERE DATE(created_at) BETWEEN DATE_SUB(DATE_SUB('{DATE}', INTERVAL 14 DAY), INTERVAL {n_weeks} WEEK) AND DATE_SUB('{DATE}', INTERVAL {n_weeks} WEEK)
        )
        SELECT
          current_fortnight.store_type AS store_type,
          COALESCE(current_fortnight.sales, 0) AS sales,
          COALESCE(previous_period_same_fortnight.sales, 0) AS previous_sales,
          COALESCE(current_fortnight.sales, 0) - COALESCE(previous_period_same_fortnight.sales, 0) AS sales_difference,
          (SAFE_DIVIDE(COALESCE(current_fortnight.sales, 0), NULLIF(COALESCE(previous_period_same_fortnight.sales, 0), 0)) - 1) * 100 AS sales_percentage_variation,

          COALESCE(current_fortnight.transactions, 0) AS transactions,
          COALESCE(previous_period_same_fortnight.transactions, 0) AS previous_transactions,
          COALESCE(current_fortnight.transactions, 0) - COALESCE(previous_period_same_fortnight.transactions, 0) AS transactions_difference,
          (SAFE_DIVIDE(COALESCE(current_fortnight.transactions, 0), NULLIF(COALESCE(previous_period_same_fortnight.transactions, 0), 0)) - 1) * 100 AS transactions_percentage_variation,

          COALESCE(current_fortnight.margin, 0) AS margin,
          COALESCE(previous_period_same_fortnight.margin, 0) AS previous_margin,
          COALESCE(current_fortnight.margin, 0) - COALESCE(previous_period_same_fortnight.margin, 0) AS margin_difference,
          (SAFE_DIVIDE(COALESCE(current_fortnight.margin, 0), NULLIF(COALESCE(previous_period_same_fortnight.margin, 0), 0)) - 1) * 100 AS margin_percentage_variation,

          COALESCE(current_fortnight.percentage_margin, 0) AS percentage_margin,
          COALESCE(previous_period_same_fortnight.percentage_margin, 0) AS previous_percentage_margin,
          COALESCE(current_fortnight.percentage_margin, 0) - COALESCE(previous_period_same_fortnight.percentage_margin, 0) AS percentage_margin_difference,
          (SAFE_DIVIDE(COALESCE(current_fortnight.percentage_margin, 0), NULLIF(COALESCE(previous_period_same_fortnight.percentage_margin, 0), 0)) - 1) * 100 AS percentage_margin_percentage_variation,

          COALESCE(current_fortnight.average_order_value, 0) AS order_value,
          COALESCE(previous_period_same_fortnight.average_order_value, 0) AS previous_order_value,
          COALESCE(current_fortnight.average_order_value, 0) - COALESCE(previous_period_same_fortnight.average_order_value, 0) AS order_value_difference,
          (SAFE_DIVIDE(COALESCE(current_fortnight.average_order_value, 0), NULLIF(COALESCE(previous_period_same_fortnight.average_order_value, 0), 0)) - 1) * 100 AS order_value_percentage_variation,

          COALESCE(current_fortnight.items_per_transaction, 0) AS items,
          COALESCE(previous_period_same_fortnight.items_per_transaction, 0) AS previous_items,
          COALESCE(current_fortnight.items_per_transaction, 0) - COALESCE(previous_period_same_fortnight.items_per_transaction, 0) AS items_difference,
          (SAFE_DIVIDE(COALESCE(current_fortnight.items_per_transaction, 0), NULLIF(COALESCE(previous_period_same_fortnight.items_per_transaction, 0), 0)) - 1) * 100 AS items_percentage_variation

        FROM current_fortnight
        LEFT JOIN previous_period_same_fortnight
        ON current_fortnight.store_type = previous_period_same_fortnight.store_type;
    """
  },
  {
    "question":
      "What is the difference in $ and % variation between "
      "total sales, "
      "total margin,"
      "percentage margin, "
      "total transactions, "
      "average order value and "
      "items per transaction, "
      "comparing the fortnight that ends on {DATE} versus the same fortnight from {n_weeks} week(s) ago",
    "query": """
      WITH current_fortnight AS 
      (
        SELECT
          SUM(sales_amount) AS sales,
          SUM(revenue) AS margin,
          SAFE_DIVIDE(SUM(revenue), NULLIF(SUM(sales_amount), 0)) * 100 AS percentage_margin,
          COUNT(DISTINCT ticket_id) AS transactions,
          SAFE_DIVIDE(SUM(sales_amount), NULLIF(COUNT(DISTINCT ticket_id), 0)) AS average_order_value,
          SAFE_DIVIDE(SUM(quantity), NULLIF(COUNT(DISTINCT ticket_id), 0)) AS items_per_transaction
        FROM fact_sales
        WHERE DATE(created_at) BETWEEN DATE_SUB('{DATE}', INTERVAL 14 DAY) AND '{DATE}'
      ),
      previous_period_same_fortnight AS 
      (
        SELECT
          SUM(sales_amount) AS sales,
          SUM(revenue) AS margin,
          SAFE_DIVIDE(SUM(revenue), NULLIF(SUM(sales_amount), 0)) * 100 AS percentage_margin,
          COUNT(DISTINCT ticket_id) AS transactions,
          SAFE_DIVIDE(SUM(sales_amount), NULLIF(COUNT(DISTINCT ticket_id), 0)) AS average_order_value,
          SAFE_DIVIDE(SUM(quantity), NULLIF(COUNT(DISTINCT ticket_id), 0)) AS items_per_transaction
        FROM fact_sales
        WHERE DATE(created_at) BETWEEN DATE_SUB(DATE_SUB('{DATE}', INTERVAL 14 DAY), INTERVAL {n_weeks} WEEK) AND DATE_SUB('{DATE}', INTERVAL {n_weeks} WEEK)
      )
      SELECT
        COALESCE(current_fortnight.sales, 0) AS sales,
        COALESCE(previous_period_same_fortnight.sales, 0) AS previous_sales,
        COALESCE(current_fortnight.sales, 0) - COALESCE(previous_period_same_fortnight.sales, 0) AS sales_difference,
        (SAFE_DIVIDE(COALESCE(current_fortnight.sales, 0), NULLIF(COALESCE(previous_period_same_fortnight.sales, 0), 0)) - 1) * 100 AS sales_percentage_variation,

        COALESCE(current_fortnight.transactions, 0) AS transactions,
        COALESCE(previous_period_same_fortnight.transactions, 0) AS previous_transactions,
        COALESCE(current_fortnight.transactions, 0) - COALESCE(previous_period_same_fortnight.transactions, 0) AS transactions_difference,
        (SAFE_DIVIDE(COALESCE(current_fortnight.transactions, 0), NULLIF(COALESCE(previous_period_same_fortnight.transactions, 0), 0)) - 1) * 100 AS transactions_percentage_variation,

        COALESCE(current_fortnight.margin, 0) AS margin,
        COALESCE(previous_period_same_fortnight.margin, 0) AS previous_margin,
        COALESCE(current_fortnight.margin, 0) - COALESCE(previous_period_same_fortnight.margin, 0) AS margin_difference,
        (SAFE_DIVIDE(COALESCE(current_fortnight.margin, 0), NULLIF(COALESCE(previous_period_same_fortnight.margin, 0), 0)) - 1) * 100 AS margin_percentage_variation,

        COALESCE(current_fortnight.percentage_margin, 0) AS percentage_margin,
        COALESCE(previous_period_same_fortnight.percentage_margin, 0) AS previous_percentage_margin,
        COALESCE(current_fortnight.percentage_margin, 0) - COALESCE(previous_period_same_fortnight.percentage_margin, 0) AS percentage_margin_difference,
        (SAFE_DIVIDE(COALESCE(current_fortnight.percentage_margin, 0), NULLIF(COALESCE(previous_period_same_fortnight.percentage_margin, 0), 0)) - 1) * 100 AS percentage_margin_percentage_variation,

        COALESCE(current_fortnight.average_order_value, 0) AS order_value,
        COALESCE(previous_period_same_fortnight.average_order_value, 0) AS previous_order_value,
        COALESCE(current_fortnight.average_order_value, 0) - COALESCE(previous_period_same_fortnight.average_order_value, 0) AS order_value_difference,
        (SAFE_DIVIDE(COALESCE(current_fortnight.average_order_value, 0), NULLIF(COALESCE(previous_period_same_fortnight.average_order_value, 0), 0)) - 1) * 100 AS order_value_percentage_variation,

        COALESCE(current_fortnight.items_per_transaction, 0) AS items,
        COALESCE(previous_period_same_fortnight.items_per_transaction, 0) AS previous_items,
        COALESCE(current_fortnight.items_per_transaction, 0) - COALESCE(previous_period_same_fortnight.items_per_transaction, 0) AS items_difference,
        (SAFE_DIVIDE(COALESCE(current_fortnight.items_per_transaction, 0), NULLIF(COALESCE(previous_period_same_fortnight.items_per_transaction, 0), 0)) - 1) * 100 AS items_percentage_variation

      FROM current_fortnight, previous_period_same_fortnight;
    """
  },
  {
    "question":
      "What was our "
      "total sales, "
      "total margin ,"
      "percentage margin "
      "for the fortnight that ends on {DATE} for the top {top_n_high_performance_stores} stores in high performance "
      "in terms of "
      "sales, "
      "margin and "
      "percentage margin "
      "and in which city is each store located",
    "query": """
      WITH ranked_stores AS 
      (
        SELECT
          ds.store_id,
          ds.store_name,
          ds.city,
          SUM(fs.sales_amount) AS total_sales,
          SUM(fs.revenue) AS total_margin,
          SAFE_DIVIDE(SUM(fs.revenue), NULLIF(SUM(fs.sales_amount), 0)) * 100 AS percentage_margin,

          -- Rankings para cada métrica
          RANK() OVER (ORDER BY SUM(fs.sales_amount) DESC) AS rank_total_sales,
          RANK() OVER (ORDER BY SUM(fs.revenue) DESC) AS rank_total_margin,
          RANK() OVER (ORDER BY SAFE_DIVIDE(SUM(fs.revenue), NULLIF(SUM(fs.sales_amount), 0)) * 100 DESC) AS rank_percentage_margin

        FROM fact_sales fs
        JOIN dim_stores ds ON fs.store_id = ds.store_id
        WHERE DATE(created_at) BETWEEN DATE_SUB('{DATE}', INTERVAL 14 DAY) AND '{DATE}'
        GROUP BY ds.store_id, ds.store_name, ds.city
        LIMIT 20
      )

      SELECT
        store_id,
        store_name,
        city,
        total_sales,
        total_margin,
        percentage_margin,

        -- Mostrar el ranking para cada métrica solo si está dentro del top N especificado
        CASE
          WHEN rank_total_sales <= {top_n_high_performance_stores}
          THEN rank_total_sales
          ELSE NULL
        END AS rank_total_sales,

        CASE
          WHEN rank_total_margin <= {top_n_high_performance_stores}
          THEN rank_total_margin
          ELSE NULL
        END AS rank_total_margin,

        CASE
          WHEN rank_percentage_margin <= {top_n_high_performance_stores}
          THEN rank_percentage_margin
          ELSE NULL
        END AS rank_percentage_margin

      FROM ranked_stores
      WHERE
        rank_total_sales <= {top_n_high_performance_stores} OR
        rank_total_margin <= {top_n_high_performance_stores} OR
        rank_percentage_margin <= {top_n_high_performance_stores}
      LIMIT 20
    """
  },
  {
    "question":
      "What was our "
      "total sales, "
      "total margin ,"
      "percentage margin "
      "for the fortnight that ends on {DATE} for the top {top_n_low_performance_stores} stores in low performance "
      "in terms of "
      "sales, "
      "margin and "
      "percentage margin "
      "and in which city is each store located",
    "query": """
      WITH ranked_stores AS 
      (
        SELECT
          ds.store_id,
          ds.store_name,
          ds.city,
          SUM(fs.sales_amount) AS total_sales,
          SUM(fs.revenue) AS total_margin,
          SAFE_DIVIDE(SUM(fs.revenue), NULLIF(SUM(fs.sales_amount), 0)) AS percentage_margin,
          RANK() OVER (ORDER BY SUM(fs.sales_amount) ASC) AS rank_total_sales,
          RANK() OVER (ORDER BY SUM(fs.revenue) ASC) AS rank_total_margin,
          RANK() OVER (ORDER BY SAFE_DIVIDE(SUM(fs.revenue), NULLIF(SUM(fs.sales_amount), 0)) ASC) AS rank_percentage_margin

        FROM fact_sales fs
        JOIN dim_stores ds ON fs.store_id = ds.store_id
        WHERE DATE(created_at) BETWEEN DATE_SUB('{DATE}', INTERVAL 14 DAY) AND '{DATE}'
        GROUP BY ds.store_id, ds.store_name, ds.city
      )

      SELECT
        store_id,
        store_name,
        city,
        COALESCE(total_sales, 0) AS total_sales,
        COALESCE(total_margin, 0) AS total_margin,
        COALESCE(percentage_margin, 0) AS percentage_margin,

        CASE WHEN rank_total_sales <= {top_n_low_performance_stores} THEN rank_total_sales ELSE NULL END AS rank_total_sales,
        CASE WHEN rank_total_margin <= {top_n_low_performance_stores} THEN rank_total_margin ELSE NULL END AS rank_total_margin,
        CASE WHEN rank_percentage_margin <= {top_n_low_performance_stores} THEN rank_percentage_margin ELSE NULL END AS rank_percentage_margin

      FROM ranked_stores
      WHERE
        rank_total_sales <= {top_n_low_performance_stores} OR
        rank_total_margin <= {top_n_low_performance_stores} OR
        rank_percentage_margin <= {top_n_low_performance_stores}
      LIMIT 20
    """
  },
  {
    "question" :
      "What was our "
      "total transactions, "
      "average order value and "
      "items per transaction "
      "for the fortnight that ends on {DATE} for the top {top_n_high_performance_stores} stores in high performance "
      "in terms of "
      "total transactions, "
      "average order value and "
      "items per transaction "
      "and in which city is each store located",
    "query": """
      WITH ranked_stores AS 
      (
        SELECT
          ds.store_id,
          ds.store_name,
          ds.city,
          COALESCE(COUNT(DISTINCT fs.ticket_id), 0) AS total_transactions,
          COALESCE(SAFE_DIVIDE(SUM(fs.sales_amount), NULLIF(COUNT(DISTINCT fs.ticket_id), 0)), 0) AS average_order_value,
          COALESCE(SAFE_DIVIDE(SUM(fs.quantity), NULLIF(COUNT(DISTINCT fs.ticket_id), 0)), 0) AS items_per_transaction,

          RANK() OVER (ORDER BY COUNT(DISTINCT fs.ticket_id) DESC) AS rank_total_transactions,
          RANK() OVER (ORDER BY SAFE_DIVIDE(SUM(fs.sales_amount), NULLIF(COUNT(DISTINCT fs.ticket_id), 0)) DESC) AS rank_average_order_value,
          RANK() OVER (ORDER BY SAFE_DIVIDE(SUM(fs.quantity), NULLIF(COUNT(DISTINCT fs.ticket_id), 0)) DESC) AS rank_items_per_transaction

        FROM fact_sales fs
        JOIN dim_stores ds ON fs.store_id = ds.store_id
        WHERE DATE(created_at) BETWEEN DATE_SUB('{DATE}', INTERVAL 14 DAY) AND '{DATE}'
        GROUP BY ds.store_id, ds.store_name, ds.city
      )

      SELECT
        store_id,
        store_name,
        city,
        total_transactions,
        average_order_value,
        items_per_transaction,
        COALESCE(CASE WHEN rank_total_transactions <= {top_n_high_performance_stores} THEN rank_total_transactions ELSE NULL END, 0) AS rank_total_transactions,
        COALESCE(CASE WHEN rank_average_order_value <= {top_n_high_performance_stores} THEN rank_average_order_value ELSE NULL END, 0) AS rank_average_order_value,
        COALESCE(CASE WHEN rank_items_per_transaction <= {top_n_high_performance_stores} THEN rank_items_per_transaction ELSE NULL END, 0) AS rank_items_per_transaction
      FROM ranked_stores
      WHERE
        rank_total_transactions <= {top_n_high_performance_stores} OR
        rank_average_order_value <= {top_n_high_performance_stores} OR
        rank_items_per_transaction <= {top_n_high_performance_stores}
      LIMIT 20
    """
  },
  {
    "question" :
      "What was our "
      "total transactions, "
      "average order value and "
      "items per transaction "
      "for the fortnight that ends on {DATE} for the top {top_n_low_performance_stores} stores in low performance "
      "in terms of "
      "total transactions, "
      "average order value and "
      "items per transaction "
      "and in which city is each store located",
    "query": """
      WITH ranked_stores AS 
      (
        SELECT
          ds.store_id,
          ds.store_name,
          ds.city,
          COUNT(DISTINCT fs.ticket_id) AS total_transactions,
          COALESCE(SAFE_DIVIDE(SUM(fs.sales_amount), NULLIF(COUNT(DISTINCT fs.ticket_id), 0)), 0) AS average_order_value,
          COALESCE(SAFE_DIVIDE(SUM(fs.quantity), NULLIF(COUNT(DISTINCT fs.ticket_id), 0)), 0) AS items_per_transaction,

          RANK() OVER (ORDER BY COUNT(DISTINCT fs.ticket_id) ASC) AS rank_total_transactions,
          RANK() OVER (ORDER BY COALESCE(SAFE_DIVIDE(SUM(fs.sales_amount), NULLIF(COUNT(DISTINCT fs.ticket_id), 0)), 0) ASC) AS rank_average_order_value,
          RANK() OVER (ORDER BY COALESCE(SAFE_DIVIDE(SUM(fs.quantity), NULLIF(COUNT(DISTINCT fs.ticket_id), 0)), 0) ASC) AS rank_items_per_transaction

        FROM fact_sales fs
        JOIN dim_stores ds ON fs.store_id = ds.store_id
        WHERE DATE(created_at) BETWEEN DATE_SUB('{DATE}', INTERVAL 14 DAY) AND '{DATE}'
        GROUP BY ds.store_id, ds.store_name, ds.city
      )

      SELECT
        store_id,
        store_name,
        city,
        COALESCE(total_transactions, 0) AS total_transactions,
        COALESCE(average_order_value, 0) AS average_order_value,
        COALESCE(items_per_transaction, 0) AS items_per_transaction,

        CASE WHEN rank_total_transactions <= {top_n_low_performance_stores} THEN rank_total_transactions ELSE NULL END AS rank_total_transactions,
        CASE WHEN rank_average_order_value <= {top_n_low_performance_stores} THEN rank_average_order_value ELSE NULL END AS rank_average_order_value,
        CASE WHEN rank_items_per_transaction <= {top_n_low_performance_stores} THEN rank_items_per_transaction ELSE NULL END AS rank_items_per_transaction

      FROM ranked_stores
      WHERE
        rank_total_transactions <= {top_n_low_performance_stores} OR
        rank_average_order_value <= {top_n_low_performance_stores} OR
        rank_items_per_transaction <= {top_n_low_performance_stores}
      LIMIT 20
    """
  },
  {
    "question":
      "What was our "
      "total sales, "
      "total margin ,"
      "percentage margin, "
      "total units sold "
      "for the fortnight that ends on {DATE} for the top {top_n_high_performance_categories} categories in high performance "
      "in terms of "
      "sales, "
      "margin and "
      "percentage margin",
    "query": """
      WITH ranked_categories AS 
      (
        SELECT
          dc.category_id,
          dc.category_name,
          COALESCE(SUM(fs.sales_amount), 0) AS total_sales,
          COALESCE(SUM(fs.revenue), 0) AS total_margin,
          SAFE_DIVIDE(COALESCE(SUM(fs.revenue), 0), NULLIF(COALESCE(SUM(fs.sales_amount), 0), 0)) * 100 AS percentage_margin,
          COALESCE(SUM(fs.quantity), 0) AS total_units_sold,

          RANK() OVER (ORDER BY COALESCE(SUM(fs.sales_amount), 0) DESC) AS rank_total_sales,
          RANK() OVER (ORDER BY COALESCE(SUM(fs.revenue), 0) DESC) AS rank_total_margin,
          RANK() OVER (ORDER BY SAFE_DIVIDE(COALESCE(SUM(fs.revenue), 0), NULLIF(COALESCE(SUM(fs.sales_amount), 0), 0)) * 100 DESC) AS rank_percentage_margin,
          RANK() OVER (ORDER BY COALESCE(SUM(fs.quantity), 0) DESC) AS rank_total_units_sold

        FROM fact_sales fs
        JOIN dim_categories dc ON fs.category_id = dc.category_id
        WHERE DATE(created_at) BETWEEN DATE_SUB('{DATE}', INTERVAL 14 DAY) AND '{DATE}'
        GROUP BY dc.category_id, dc.category_name
      )

      SELECT
        category_id,
        category_name,
        total_sales,
        total_margin,
        percentage_margin,
        total_units_sold,
        CASE WHEN rank_total_sales <= {top_n_high_performance_categories} THEN rank_total_sales ELSE NULL END AS rank_total_sales,
        CASE WHEN rank_total_margin <= {top_n_high_performance_categories} THEN rank_total_margin ELSE NULL END AS rank_total_margin,
        CASE WHEN rank_percentage_margin <= {top_n_high_performance_categories} THEN rank_percentage_margin ELSE NULL END AS rank_percentage_margin,
        CASE WHEN rank_total_units_sold <= {top_n_high_performance_categories} THEN rank_total_units_sold ELSE NULL END AS rank_total_units_sold
      FROM ranked_categories
      WHERE
        rank_total_sales <= {top_n_high_performance_categories} OR
        rank_total_margin <= {top_n_high_performance_categories} OR
        rank_percentage_margin <= {top_n_high_performance_categories} OR
        rank_total_units_sold <= {top_n_high_performance_categories}
      LIMIT 20
    """
  },
  {
    "question":
      "What was our "
      "total sales, "
      "total margin ,"
      "percentage margin, "
      "total units sold "
      "for the fortnight that ends on {DATE} for the top {top_n_low_performance_categories} categories in low performance "
      "in terms of "
      "sales, "
      "margin and "
      "percentage margin",
    "query": """
      WITH ranked_categories AS 
      (
        SELECT
          dc.category_id,
          dc.category_name,
          COALESCE(SUM(fs.sales_amount), 0) AS total_sales,
          COALESCE(SUM(fs.revenue), 0) AS total_margin,
          SAFE_DIVIDE(COALESCE(SUM(fs.revenue), 0), NULLIF(SUM(fs.sales_amount), 0)) * 100 AS percentage_margin,
          COALESCE(SUM(fs.quantity), 0) AS total_units_sold,

          RANK() OVER (ORDER BY COALESCE(SUM(fs.sales_amount), 0) ASC) AS rank_total_sales,
          RANK() OVER (ORDER BY COALESCE(SUM(fs.revenue), 0) ASC) AS rank_total_margin,
          RANK() OVER (ORDER BY SAFE_DIVIDE(COALESCE(SUM(fs.revenue), 0), NULLIF(SUM(fs.sales_amount), 0)) * 100 ASC) AS rank_percentage_margin,
          RANK() OVER (ORDER BY COALESCE(SUM(fs.quantity), 0) ASC) AS rank_total_units_sold

        FROM fact_sales fs
        JOIN dim_categories dc ON fs.category_id = dc.category_id
        WHERE DATE(created_at) BETWEEN DATE_SUB('{DATE}', INTERVAL 14 DAY) AND '{DATE}'
        GROUP BY dc.category_id, dc.category_name
      )

      SELECT
        category_id,
        category_name,
        total_sales,
        total_margin,
        percentage_margin,
        total_units_sold,
        CASE WHEN rank_total_sales <= {top_n_low_performance_categories} THEN rank_total_sales ELSE NULL END AS rank_total_sales,
        CASE WHEN rank_total_margin <= {top_n_low_performance_categories} THEN rank_total_margin ELSE NULL END AS rank_total_margin,
        CASE WHEN rank_percentage_margin <= {top_n_low_performance_categories} THEN rank_percentage_margin ELSE NULL END AS rank_percentage_margin,
        CASE WHEN rank_total_units_sold <= {top_n_low_performance_categories} THEN rank_total_units_sold ELSE NULL END AS rank_total_units_sold
      FROM ranked_categories
      WHERE
        rank_total_sales <= {top_n_low_performance_categories} OR
        rank_total_margin <= {top_n_low_performance_categories} OR
        rank_percentage_margin <= {top_n_low_performance_categories} OR
        rank_total_units_sold <= {top_n_low_performance_categories}
      LIMIT 20
    """
  },
  {
    "question":
      "What was our "
      "total sales, "
      "total margin ,"
      "percentage margin and "
      "total units sold "
      "for the fortnight that ends on {DATE} for the top {top_n_high_performance_items} products in high performance "
      "in terms of "
      "sales, "
      "margin "
      "percentage margin and "
      "units sold",
    "query": """
      WITH ranked_items AS 
      (
        SELECT
          di.item_id,
          di.item_name,
          COALESCE(SUM(fs.sales_amount), 0) AS total_sales,
          COALESCE(SUM(fs.revenue), 0) AS total_margin,
          COALESCE(SAFE_DIVIDE(SUM(fs.revenue), NULLIF(SUM(fs.sales_amount), 0)) * 100, 0) AS percentage_margin,
          COALESCE(SUM(fs.quantity), 0) AS total_units_sold,

          RANK() OVER (ORDER BY COALESCE(SUM(fs.sales_amount), 0) DESC) AS rank_total_sales,
          RANK() OVER (ORDER BY COALESCE(SUM(fs.revenue), 0) DESC) AS rank_total_margin,
          RANK() OVER (ORDER BY COALESCE(SAFE_DIVIDE(SUM(fs.revenue), NULLIF(SUM(fs.sales_amount), 0)) * 100, 0) DESC) AS rank_percentage_margin,
          RANK() OVER (ORDER BY COALESCE(SUM(fs.quantity), 0) DESC) AS rank_total_units_sold

        FROM fact_sales fs
        JOIN dim_items di ON fs.item_id = di.item_id
        WHERE DATE(created_at) BETWEEN DATE_SUB('{DATE}', INTERVAL 14 DAY) AND '{DATE}'
        GROUP BY di.item_id, di.item_name
      )

      SELECT
        item_id, item_name, total_sales, total_margin, percentage_margin, total_units_sold,
        CASE WHEN rank_total_sales <= {top_n_high_performance_items} THEN rank_total_sales ELSE NULL END AS rank_total_sales,
        CASE WHEN rank_total_margin <= {top_n_high_performance_items} THEN rank_total_margin ELSE NULL END AS rank_total_margin,
        CASE WHEN rank_percentage_margin <= {top_n_high_performance_items} THEN rank_percentage_margin ELSE NULL END AS rank_percentage_margin,
        CASE WHEN rank_total_units_sold <= {top_n_high_performance_items} THEN rank_total_units_sold ELSE NULL END AS rank_total_units_sold
      FROM ranked_items
      WHERE
        rank_total_sales <= {top_n_high_performance_items} OR
        rank_total_margin <= {top_n_high_performance_items} OR
        rank_percentage_margin <= {top_n_high_performance_items} OR
        rank_total_units_sold <= {top_n_high_performance_items}
      LIMIT 20
    """
  },
  {
    "question":
      "What was our "
      "total sales, "
      "total margin ,"
      "percentage margin and "
      "total units sold "
      "for the fortnight that ends on {DATE} for the top {top_n_low_performance_items} products in low performance "
      "in terms of "
      "sales, "
      "margin "
      "percentage margin and "
      "units sold",
    "query": """
      WITH ranked_items AS 
      (
        SELECT
          di.item_id,
          di.item_name,
          COALESCE(SUM(fs.sales_amount), 0) AS total_sales,
          COALESCE(SUM(fs.revenue), 0) AS total_margin,
          COALESCE(SAFE_DIVIDE(SUM(fs.revenue), NULLIF(SUM(fs.sales_amount), 0)) * 100, 0) AS percentage_margin,
          COALESCE(SUM(fs.quantity), 0) AS total_units_sold,

          RANK() OVER (ORDER BY COALESCE(SUM(fs.sales_amount), 0) ASC) AS rank_total_sales,
          RANK() OVER (ORDER BY COALESCE(SUM(fs.revenue), 0) ASC) AS rank_total_margin,
          RANK() OVER (ORDER BY COALESCE(SAFE_DIVIDE(SUM(fs.revenue), NULLIF(SUM(fs.sales_amount), 0)) * 100, 0) ASC) AS rank_percentage_margin,
          RANK() OVER (ORDER BY COALESCE(SUM(fs.quantity), 0) ASC) AS rank_total_units_sold

        FROM fact_sales fs
        JOIN dim_items di ON fs.item_id = di.item_id
        WHERE DATE(created_at) BETWEEN DATE_SUB('{DATE}', INTERVAL 14 DAY) AND '{DATE}'
        GROUP BY di.item_id, di.item_name
      )

      SELECT
        item_id, item_name, total_sales, total_margin, percentage_margin, total_units_sold,
        CASE WHEN rank_total_sales <= {top_n_low_performance_items} THEN rank_total_sales ELSE NULL END AS rank_total_sales,
        CASE WHEN rank_total_margin <= {top_n_low_performance_items} THEN rank_total_margin ELSE NULL END AS rank_total_margin,
        CASE WHEN rank_percentage_margin <= {top_n_low_performance_items} THEN rank_percentage_margin ELSE NULL END AS rank_percentage_margin,
        CASE WHEN rank_total_units_sold <= {top_n_low_performance_items} THEN rank_total_units_sold ELSE NULL END AS rank_total_units_sold
      FROM ranked_items
      WHERE
        rank_total_sales <= {top_n_low_performance_items} OR
        rank_total_margin <= {top_n_low_performance_items} OR
        rank_percentage_margin <= {top_n_low_performance_items} OR
        rank_total_units_sold <= {top_n_low_performance_items}
      LIMIT 20
    """
  },
  {
    "question": 
      "What was our "
      "total sales, "
      "total margin ,"
      "percentage margin and "
      "total units sold "
      "for the fortnight that ends on {DATE} for the top {top_n_high_performance_vendors} vendors in high performance "
      "in terms of "
      "sales, "
      "margin "
      "percentage margin and "
      "units sold",
    "query": """
      WITH ranked_vendors AS 
      (
        SELECT
          dv.vendor_id,
          dv.vendor_name,
          COALESCE(SUM(fs.sales_amount), 0) AS total_sales,
          COALESCE(SUM(fs.revenue), 0) AS total_margin,
          COALESCE(SAFE_DIVIDE(SUM(fs.revenue), NULLIF(SUM(fs.sales_amount), 0)) * 100, 0) AS percentage_margin,
          COALESCE(SUM(fs.quantity), 0) AS total_units_sold,

          RANK() OVER (ORDER BY COALESCE(SUM(fs.sales_amount), 0) DESC) AS rank_total_sales,
          RANK() OVER (ORDER BY COALESCE(SUM(fs.revenue), 0) DESC) AS rank_total_margin,
          RANK() OVER (ORDER BY COALESCE(SAFE_DIVIDE(SUM(fs.revenue), NULLIF(SUM(fs.sales_amount), 0)) * 100, 0) DESC) AS rank_percentage_margin,
          RANK() OVER (ORDER BY COALESCE(SUM(fs.quantity), 0) DESC) AS rank_total_units_sold

        FROM fact_sales fs
        JOIN dim_vendors dv ON fs.vendor_id = dv.vendor_id
        WHERE DATE(created_at) BETWEEN DATE_SUB('{DATE}', INTERVAL 14 DAY) AND '{DATE}'
        GROUP BY dv.vendor_id, dv.vendor_name
      )

      SELECT
        vendor_id, vendor_name, total_sales, total_margin, percentage_margin, total_units_sold,
        CASE WHEN rank_total_sales <= {top_n_high_performance_vendors} THEN rank_total_sales ELSE NULL END AS rank_total_sales,
        CASE WHEN rank_total_margin <= {top_n_high_performance_vendors} THEN rank_total_margin ELSE NULL END AS rank_total_margin,
        CASE WHEN rank_percentage_margin <= {top_n_high_performance_vendors} THEN rank_percentage_margin ELSE NULL END AS rank_percentage_margin,
        CASE WHEN rank_total_units_sold <= {top_n_high_performance_vendors} THEN rank_total_units_sold ELSE NULL END AS rank_total_units_sold
      FROM ranked_vendors
      WHERE
        rank_total_sales <= {top_n_high_performance_vendors} OR
        rank_total_margin <= {top_n_high_performance_vendors} OR
        rank_percentage_margin <= {top_n_high_performance_vendors} OR
        rank_total_units_sold <= {top_n_high_performance_vendors}
      LIMIT 20
    """
  },
  {
    "question":
      "What was our "
      "total sales, "
      "total margin ,"
      "percentage margin and "
      "total units sold "
      "for the fortnight that ends on {DATE} for the top {top_n_low_performance_vendors} vendors in low performance "
      "in terms of "
      "sales, "
      "margin "
      "percentage margin and "
      "units sold",
    "query": """
      WITH ranked_vendors AS 
      (
        SELECT
          dv.vendor_id,
          dv.vendor_name,
          COALESCE(SUM(fs.sales_amount), 0) AS total_sales,
          COALESCE(SUM(fs.revenue), 0) AS total_margin,
          COALESCE(SAFE_DIVIDE(SUM(fs.revenue), NULLIF(SUM(fs.sales_amount), 0)) * 100, 0) AS percentage_margin,
          COALESCE(SUM(fs.quantity), 0) AS total_units_sold,

          RANK() OVER (ORDER BY COALESCE(SUM(fs.sales_amount), 0) ASC) AS rank_total_sales,
          RANK() OVER (ORDER BY COALESCE(SUM(fs.revenue), 0) ASC) AS rank_total_margin,
          RANK() OVER (ORDER BY COALESCE(SAFE_DIVIDE(SUM(fs.revenue), NULLIF(SUM(fs.sales_amount), 0)) * 100, 0) ASC) AS rank_percentage_margin,
          RANK() OVER (ORDER BY COALESCE(SUM(fs.quantity), 0) ASC) AS rank_total_units_sold

        FROM fact_sales fs
        JOIN dim_vendors dv ON fs.vendor_id = dv.vendor_id
        WHERE DATE(created_at) BETWEEN DATE_SUB('{DATE}', INTERVAL 14 DAY) AND '{DATE}'
        GROUP BY dv.vendor_id, dv.vendor_name
      )

      SELECT
        vendor_id, vendor_name, total_sales, total_margin, percentage_margin, total_units_sold,
        CASE WHEN rank_total_sales <= {top_n_low_performance_vendors} THEN rank_total_sales ELSE NULL END AS rank_total_sales,
        CASE WHEN rank_total_margin <= {top_n_low_performance_vendors} THEN rank_total_margin ELSE NULL END AS rank_total_margin,
        CASE WHEN rank_percentage_margin <= {top_n_low_performance_vendors} THEN rank_percentage_margin ELSE NULL END AS rank_percentage_margin,
        CASE WHEN rank_total_units_sold <= {top_n_low_performance_vendors} THEN rank_total_units_sold ELSE NULL END AS rank_total_units_sold
      FROM ranked_vendors
      WHERE
        rank_total_sales <= {top_n_low_performance_vendors} OR
        rank_total_margin <= {top_n_low_performance_vendors} OR
        rank_percentage_margin <= {top_n_low_performance_vendors} OR
        rank_total_units_sold <= {top_n_low_performance_vendors}
      LIMIT 20
    """
  },
  {
    "question":
      "What was our "
      "total sales, "
      "total margin ,"
      "percentage margin "
      "for the fortnight that ends on {DATE} for city?",
    "query": """
      SELECT
        ds.city,
        SUM(fs.sales_amount) AS total_sales,
        SUM(fs.revenue) AS total_margin,
        SAFE_DIVIDE(SUM(fs.revenue), NULLIF(SUM(fs.sales_amount), 0)) * 100 AS percentage_margin,
      FROM fact_sales fs
      JOIN dim_stores ds ON fs.store_id = ds.store_id
      WHERE DATE(created_at) BETWEEN DATE_SUB('{DATE}', INTERVAL 14 DAY) AND '{DATE}'
      GROUP BY ds.city
      LIMIT 20
    """
  },
  {
    "question":
      "What was our "
      "total sales, "
      "total margin ,"
      "percentage margin, "
      "total_transactions, "
      "average_order_value and "
      "items_per_transaction "
      "for the fortnight that ends on {DATE} for all stores and in which city is each store located?",
    "query": """
      SELECT
        ds.store_id,
        ds.store_name,
        ds.city,
        COALESCE(SUM(sales_amount), 0) AS total_sales,
        COALESCE(SUM(revenue), 0) AS total_margin,
        SAFE_DIVIDE(COALESCE(SUM(revenue), 0), NULLIF(SUM(sales_amount), 0)) * 100 AS percentage_margin,
        COUNT(DISTINCT ticket_id) AS total_transactions,
        SAFE_DIVIDE(COALESCE(SUM(sales_amount), 0), NULLIF(COUNT(DISTINCT ticket_id), 0)) AS average_order_value,
        SAFE_DIVIDE(COALESCE(SUM(quantity), 0), NULLIF(COUNT(DISTINCT ticket_id), 0)) AS items_per_transaction
      FROM fact_sales fs
      JOIN dim_stores ds ON fs.store_id = ds.store_id
      WHERE DATE(created_at) BETWEEN DATE_SUB('{DATE}', INTERVAL 14 DAY) AND '{DATE}'
      GROUP BY ds.store_id, ds.store_name, ds.city
      LIMIT 20
    """
  },
  {
    "question":
      "What was our "
      "total sales, "
      "total margin, "
      "percentage margin, "
      "total units sold "
      "for the fortnight that ends on {DATE} for all categories ",
    "query": """
      SELECT
        dc.category_id,
        dc.category_name,
        COALESCE(SUM(fs.sales_amount), 0) AS total_sales,
        COALESCE(SUM(fs.revenue), 0) AS total_margin,
        SAFE_DIVIDE(COALESCE(SUM(fs.revenue), 0), NULLIF(COALESCE(SUM(fs.sales_amount), 0), 0)) * 100 AS percentage_margin,
        COALESCE(SUM(fs.quantity), 0) AS total_units_sold,
      FROM fact_sales fs
      JOIN dim_categories dc ON fs.category_id = dc.category_id
      WHERE DATE(created_at) BETWEEN DATE_SUB('{DATE}', INTERVAL 14 DAY) AND '{DATE}'
      GROUP BY dc.category_id, dc.category_name
      LIMIT 20
    """
  },
  {
    "question":
      "What was our "
      "total actual sales, "
      "total sales forecast, "
      "lower bound, "
      "upper bound, "
      "difference between actual sales and forecast sales, "
      "percentage difference between actual sales and forecast sales, "
      "for the fortnight that ends on {DATE}?",
    "query": """
      WITH forecast AS 
      (
        SELECT 
          SUM(forecast_value) AS forecast_value, 
          SUM(confidence_interval_lower_bound) AS lower_bound, 
          SUM(confidence_interval_upper_bound) AS upper_bound 
        FROM 
          ML.FORECAST(MODEL modelo_arima_dia, STRUCT(40 AS horizon)) 
        WHERE DATE(forecast_timestamp) BETWEEN DATE_SUB('{DATE}', INTERVAL 14 DAY) AND '{DATE}'
      ), 
      actual AS 
      (
        SELECT 
          SUM(sales_amount) AS total_sales 
        FROM 
          fact_sales 
        WHERE DATE(created_at) BETWEEN DATE_SUB('{DATE}', INTERVAL 14 DAY) AND '{DATE}'
      ) 
      SELECT 
        COALESCE(a.total_sales, 0) AS actual_total_sales, 
        COALESCE(f.forecast_value, 0) AS total_sales_forecast, 
        COALESCE(f.lower_bound, 0) AS lower_bound, 
        COALESCE(f.upper_bound, 0) AS upper_bound,
        (COALESCE(a.total_sales, 0) - COALESCE(f.forecast_value, 0)) AS difference,
        COALESCE((((COALESCE(a.total_sales, 0) / NULLIF(f.forecast_value, 0)) - 1) * 100), 0) AS percentage
      FROM 
        forecast f, actual a
    """
  },
  {
    "question":
      "What was our "
      "total actual cost, "
      "total cost forecast, "
      "lower bound, "
      "upper bound, "
      "difference between actual cost and forecast cost, "
      "percentage difference between actual cost and forecast cost, "
      "for the fortnight that ends on {DATE}?",
    "query": """
      WITH forecast AS 
      (
        SELECT 
          SUM(forecast_value) AS forecast_value, 
          SUM(confidence_interval_lower_bound) AS lower_bound, 
          SUM(confidence_interval_upper_bound) AS upper_bound 
        FROM 
          ML.FORECAST(MODEL modelo_arima_dia_cost, STRUCT(40 AS horizon)) 
        WHERE DATE(forecast_timestamp) BETWEEN DATE_SUB('{DATE}', INTERVAL 14 DAY) AND '{DATE}'
      ), 
      actual AS 
      (
        SELECT 
          SUM(cost) AS total_cost 
        FROM 
          fact_sales 
        WHERE DATE(created_at) BETWEEN DATE_SUB('{DATE}', INTERVAL 14 DAY) AND '{DATE}'
      ) 
      SELECT 
        COALESCE(a.total_cost, 0) AS actual_total_cost, 
        COALESCE(f.forecast_value, 0) AS total_cost_forecast, 
        COALESCE(f.lower_bound, 0) AS lower_bound, 
        COALESCE(f.upper_bound, 0) AS upper_bound,
        (COALESCE(a.total_cost, 0) - COALESCE(f.forecast_value, 0)) AS difference,
        COALESCE((((COALESCE(a.total_cost, 0) / NULLIF(f.forecast_value, 0)) - 1) * 100), 0) AS percentage
      FROM 
        forecast f, actual a
    """
  },
  {
    "question":
      "What was our "
      "total actual revenue, "
      "total revenue forecast, "
      "lower bound, "
      "upper bound, "
      "difference between actual revenue and forecast revenue, "
      "percentage difference between actual revenue and forecast revenue, "
      "for the fortnight that ends on {DATE}?",
    "query": """
      WITH forecast AS 
      (
        WITH sales AS 
        (
          SELECT * 
          FROM ML.FORECAST(MODEL modelo_arima_dia, STRUCT(30 AS horizon, 0.99 AS confidence_level))
          WHERE DATE(forecast_timestamp) BETWEEN DATE_SUB('{DATE}', INTERVAL 14 DAY) AND '{DATE}'
        ), 
        costs AS 
        (
          SELECT * 
          FROM ML.FORECAST(MODEL modelo_arima_dia_cost, STRUCT(30 AS horizon, 0.99 AS confidence_level))
          WHERE DATE(forecast_timestamp) BETWEEN DATE_SUB('{DATE}', INTERVAL 14 DAY) AND '{DATE}'
      
        ) 
        SELECT 
          SUM(s.forecast_value) AS total_sales, 
          SUM(c.forecast_value) AS total_cost, 
          (SUM(s.forecast_value) - SUM(c.forecast_value)) AS revenue, 
          (SUM(s.prediction_interval_lower_bound) - SUM(c.prediction_interval_lower_bound)) AS prediction_interval_lower_bound, 
          (SUM(s.prediction_interval_upper_bound) - SUM(c.prediction_interval_upper_bound)) AS prediction_interval_upper_bound 
        FROM sales s, costs c
      ), 
      actual AS 
      (
        SELECT 
          SUM(revenue) AS revenue 
        FROM fact_sales 
        WHERE DATE(created_at) BETWEEN DATE_SUB('{DATE}', INTERVAL 14 DAY) AND '{DATE}'
      ) 
      SELECT 
        COALESCE(a.revenue, 0) AS actual_revenue, 
        COALESCE(f.revenue, 0) AS revenue_forecast,
        COALESCE(f.prediction_interval_lower_bound, 0) AS lower_bound, 
        COALESCE(f.prediction_interval_upper_bound, 0) AS upper_bound,
        (COALESCE(a.revenue, 0) - COALESCE(f.revenue, 0)) AS difference,
        COALESCE((((COALESCE(a.revenue, 0) / NULLIF(f.revenue, 0)) - 1) * 100), 0) AS percentage 
      FROM forecast f, actual a
    """
  },
  {
    "question":
      "What was our "
      "actual margin, "
      "forecast margin, "
      "lower bound, "
      "upper bound, "
      "difference between actual margin and forecast margin, "
      "percentage difference between actual margin and forecast margin, "
      "for the fortnight that ends on {DATE}?",
    "query": """
      WITH forecast AS 
      (
        WITH sales AS 
        (
          SELECT * 
          FROM ML.FORECAST(MODEL modelo_arima_dia, STRUCT(30 AS horizon, 0.99 AS confidence_level))
          WHERE DATE(forecast_timestamp) BETWEEN DATE_SUB('{DATE}', INTERVAL 14 DAY) AND '{DATE}'
        ), 
        costs AS 
        (
          SELECT * 
          FROM ML.FORECAST(MODEL modelo_arima_dia_cost, STRUCT(30 AS horizon, 0.99 AS confidence_level))
          WHERE DATE(forecast_timestamp) BETWEEN DATE_SUB('{DATE}', INTERVAL 14 DAY) AND '{DATE}'
        ) 
        SELECT 
          SUM(s.forecast_value) AS total_sales, 
          SUM(c.forecast_value) AS total_cost,  
          (SUM(s.forecast_value) - SUM(c.forecast_value)) / NULLIF(SUM(s.forecast_value), 0) AS margin, 
          (SUM(s.prediction_interval_lower_bound) - SUM(c.prediction_interval_lower_bound)) / NULLIF(SUM(s.prediction_interval_lower_bound), 0) AS prediction_interval_lower_bound, 
          (SUM(s.prediction_interval_upper_bound) - SUM(c.prediction_interval_upper_bound)) / NULLIF(SUM(s.prediction_interval_upper_bound), 0) AS prediction_interval_upper_bound 
        FROM sales s, costs c
      ), 
      actual AS 
      (
        SELECT 
          (SUM(revenue) / NULLIF(SUM(sales_amount), 0)) AS margin  
        FROM fact_sales 
        WHERE DATE(created_at) BETWEEN DATE_SUB('{DATE}', INTERVAL 14 DAY) AND '{DATE}'
      ) 
      SELECT 
        COALESCE(a.margin, 0) AS actual_margen, 
        COALESCE(f.margin, 0) AS margen_forecast,
        COALESCE(f.prediction_interval_lower_bound, 0) AS lower_bound, 
        COALESCE(f.prediction_interval_upper_bound, 0) AS upper_bound,
        (COALESCE(a.margin, 0) - COALESCE(f.margin, 0)) AS difference,
        COALESCE((((COALESCE(a.margin, 0) / NULLIF(f.margin, 0)) - 1) * 100), 0) AS percentage 
        FROM forecast f, actual a
    """
  },
  {
    "question":
      "What was our "
      "total actual sales, "
      "total sales forecast, "
      "lower bound, "
      "upper bound, "
      "difference between actual sales and forecast sales, "
      "percentage difference between actual sales and forecast sales, "
      "for the fortnight that ends on {DATE} for category?",
    "query": """
      WITH forecast AS 
      (
        SELECT 
          category_name, 
          SUM(forecast_value) AS forecast_value, 
          SUM(confidence_interval_lower_bound) AS lower_bound, 
          SUM(confidence_interval_upper_bound) AS upper_bound 
        FROM ML.FORECAST(MODEL modelo_arima_dia_categories, STRUCT(40 AS horizon)) 
        WHERE DATE(forecast_timestamp) BETWEEN DATE_SUB('{DATE}', INTERVAL 14 DAY) AND '{DATE}'
        GROUP BY category_name
      ), 
      actual AS 
      (
        SELECT 
          category_name, 
          SUM(sales_amount) AS total_sales 
        FROM fact_sales s 
        JOIN dim_categories c ON s.category_id = c.category_id 
        WHERE DATE(created_at) BETWEEN DATE_SUB('{DATE}', INTERVAL 14 DAY) AND '{DATE}'
        GROUP BY category_name
      ) 
      SELECT 
        COALESCE(f.category_name, '') AS category_name, 
        COALESCE(a.total_sales, 0) AS actual_total_sales,
        COALESCE(f.forecast_value, 0) AS total_sales_forecast, 
        COALESCE(f.lower_bound, 0) AS lower_bound, 
        COALESCE(f.upper_bound, 0) AS upper_bound,
        (COALESCE(a.total_sales, 0) - COALESCE(f.forecast_value, 0)) AS difference,
        COALESCE((((COALESCE(a.total_sales, 0) / NULLIF(f.forecast_value, 0)) - 1) * 100), 0) AS percentage
      FROM forecast f 
      LEFT JOIN actual a ON f.category_name = a.category_name
      ORDER BY actual_total_sales DESC
      LIMIT 20
    """
  },
  {
    "question":
      "What was our "
      "total actual sales, "
      "total sales forecast, "
      "lower bound, "
      "upper bound, "
      "difference between actual sales and forecast sales, "
      "percentage difference between actual sales and forecast sales, "
      "for the fortnight that ends on {DATE} for store?",
    "query": """
      WITH forecast AS 
      (
        SELECT 
          store_name,  
          SUM(forecast_value) AS forecast_value, 
          SUM(confidence_interval_lower_bound) AS lower_bound, 
          SUM(confidence_interval_upper_bound) AS upper_bound 
        FROM ML.FORECAST(MODEL modelo_arima_dia_stores, STRUCT(40 AS horizon)) 
        WHERE DATE(forecast_timestamp) BETWEEN DATE_SUB('{DATE}', INTERVAL 14 DAY) AND '{DATE}'
        GROUP BY store_name
      ), 
      actual AS 
      (
        SELECT 
          store_name, 
          SUM(sales_amount) AS total_sales 
        FROM fact_sales s 
        JOIN dim_stores st ON s.store_id = st.store_id 
        WHERE 
          EXTRACT(DATE FROM created_at) = '{DATE}'
        GROUP BY store_name
      ) 
      SELECT 
        COALESCE(f.store_name, '') AS store_name, 
        COALESCE(a.total_sales, 0) AS actual_total_sales, 
        COALESCE(f.forecast_value, 0) AS total_sales_forecast,
        COALESCE(f.lower_bound, 0) AS lower_bound,
        COALESCE(f.upper_bound, 0) AS upper_bound,
        (COALESCE(a.total_sales, 0) - COALESCE(f.forecast_value, 0)) AS difference,
        COALESCE((((COALESCE(a.total_sales, 0) / NULLIF(f.forecast_value, 0)) - 1) * 100), 0) AS percentage
      FROM forecast f 
      LEFT JOIN actual a ON f.store_name = a.store_name
      ORDER BY actual_total_sales DESC
      LIMIT 20
    """
  },
  {
    "question":
      "What will be our "
      "total sales, "
      "lower bound, "
      "upper bound "
      "for the next fortnight?",
    "query": """
      SELECT 
        COALESCE(SUM(forecast_value), 0) AS total_sales, 
        COALESCE(SUM(confidence_interval_lower_bound), 0) AS lower_bound, 
        COALESCE(SUM(confidence_interval_upper_bound), 0) AS upper_bound 
      FROM 
        ML.FORECAST(MODEL modelo_arima_dia, STRUCT(40 AS horizon)) 
      WHERE DATE(forecast_timestamp) BETWEEN DATE_ADD('{DATE}', INTERVAL 1 DAY) AND DATE_ADD('{DATE}', INTERVAL 15 DAY)
    """
  },
  {
    "question":
      "What will be our "
      "total cost, "
      "lower bound, "
      "upper bound "
      "for the next fortnight?",
    "query": """
      SELECT 
        COALESCE(SUM(forecast_value), 0) AS total_cost,
        COALESCE(SUM(confidence_interval_lower_bound), 0) AS lower_bound, 
        COALESCE(SUM(confidence_interval_upper_bound), 0) AS upper_bound 
      FROM 
        ML.FORECAST(MODEL modelo_arima_dia_cost, STRUCT(40 AS horizon)) 
        WHERE DATE(forecast_timestamp) BETWEEN DATE_ADD('{DATE}', INTERVAL 1 DAY) AND DATE_ADD('{DATE}', INTERVAL 15 DAY)
    """
  },
  {
    "question":
      "What will be our "
      "total revenue, "
      "lower bound, "
      "upper bound "
      "for the next fortnight?",
    "query": """
      WITH sales AS 
      (
        SELECT * 
        FROM ML.FORECAST(MODEL modelo_arima_dia, STRUCT(30 AS horizon, 0.99 AS confidence_level))
        WHERE DATE(forecast_timestamp) BETWEEN DATE_ADD('{DATE}', INTERVAL 1 DAY) AND DATE_ADD('{DATE}', INTERVAL 15 DAY)
      ), 
      costs AS 
      (
        SELECT * 
        FROM ML.FORECAST(MODEL modelo_arima_dia_cost, STRUCT(30 AS horizon, 0.99 AS confidence_level))
        WHERE DATE(forecast_timestamp) BETWEEN DATE_ADD('{DATE}', INTERVAL 1 DAY) AND DATE_ADD('{DATE}', INTERVAL 15 DAY)
      ) 
      SELECT 
        (COALESCE(SUM(s.forecast_value), 0) - COALESCE(SUM(c.forecast_value), 0)) AS revenue, 
        (COALESCE(SUM(s.prediction_interval_lower_bound), 0) - COALESCE(SUM(c.prediction_interval_lower_bound), 0)) AS prediction_interval_lower_bound, 
        (COALESCE(SUM(s.prediction_interval_upper_bound), 0) - COALESCE(SUM(c.prediction_interval_upper_bound), 0)) AS prediction_interval_upper_bound 
      FROM sales s, costs c
    """
  },
  {
    "question":
      "What will be our "
      "margin, "
      "lower bound, "
      "upper bound "
      "for the next fortnight?",
    "query": """
      WITH sales AS 
      (
        SELECT * 
        FROM ML.FORECAST(MODEL modelo_arima_dia, STRUCT(30 AS horizon, 0.99 AS confidence_level))
        WHERE DATE(forecast_timestamp) BETWEEN DATE_ADD('{DATE}', INTERVAL 1 DAY) AND DATE_ADD('{DATE}', INTERVAL 15 DAY)
      ), 
      costs AS 
      (
        SELECT * 
        FROM ML.FORECAST(MODEL modelo_arima_dia_cost, STRUCT(30 AS horizon, 0.99 AS confidence_level))
        WHERE DATE(forecast_timestamp) BETWEEN DATE_ADD('{DATE}', INTERVAL 1 DAY) AND DATE_ADD('{DATE}', INTERVAL 15 DAY)
      ) 
      SELECT 
        (COALESCE(SUM(s.forecast_value), 0) - COALESCE(SUM(c.forecast_value), 0)) / NULLIF(SUM(s.forecast_value), 0) AS margin, 
        (COALESCE(SUM(s.prediction_interval_lower_bound), 0) - COALESCE(SUM(c.prediction_interval_lower_bound), 0)) / NULLIF(SUM(s.prediction_interval_lower_bound), 0) AS prediction_interval_lower_bound, 
        (COALESCE(SUM(s.prediction_interval_upper_bound), 0) - COALESCE(SUM(c.prediction_interval_upper_bound), 0)) / NULLIF(SUM(s.prediction_interval_upper_bound), 0) AS prediction_interval_upper_bound 
      FROM sales s, costs c
    """
  },
  {
    "question":
      "What will be our "
      "total sales, "
      "lower bound, "
      "upper bound "
      "for the next fortnight for category?",
    "query": """
      SELECT 
        COALESCE(category_name, '') AS category_name, 
        COALESCE(SUM(forecast_value), 0) AS total_sales,
        COALESCE(SUM(confidence_interval_lower_bound), 0) AS lower_bound, 
        COALESCE(SUM(confidence_interval_upper_bound), 0) AS upper_bound 
      FROM ML.FORECAST(MODEL modelo_arima_dia_categories, STRUCT(40 AS horizon)) 
      WHERE DATE(forecast_timestamp) BETWEEN DATE_ADD('{DATE}', INTERVAL 1 DAY) AND DATE_ADD('{DATE}', INTERVAL 15 DAY)
      GROUP BY category_name
      ORDER BY total_sales DESC
      LIMIT 20
    """
  },
  {
    "question":
      "What will be our "
      "total sales, "
      "lower bound, "
      "upper bound "
      "for the next fortnight for store?",
    "query": """
      SELECT 
        COALESCE(store_name, '') AS store_name, 
        COALESCE(SUM(forecast_value), 0) AS total_sales,
        COALESCE(SUM(confidence_interval_lower_bound), 0) AS lower_bound, 
        COALESCE(SUM(confidence_interval_upper_bound), 0) AS upper_bound 
      FROM ML.FORECAST(MODEL modelo_arima_dia_stores, STRUCT(40 AS horizon)) 
      WHERE DATE(forecast_timestamp) BETWEEN DATE_ADD('{DATE}', INTERVAL 1 DAY) AND DATE_ADD('{DATE}', INTERVAL 15 DAY)
      GROUP BY store_name
      ORDER BY total_sales DESC
      LIMIT 20
    """
  },
]

def get_default_questions(default_questions=default_questions):
  return default_questions
