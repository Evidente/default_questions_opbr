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
      "from {DATE}?",
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
      WHERE DATE(created_at) = '{DATE}';
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
      "comparing {DATE} versus the same weekday from {n_weeks} week(s) ago, "
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
      current_day AS 
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
        WHERE DATE(fact_sales.created_at) = '{DATE}'
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
        WHERE DATE(fact_sales.created_at) = '{DATE}'
      ),
      previous_period_same_day AS 
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
        WHERE DATE(fact_sales.created_at) = DATE_SUB('{DATE}', INTERVAL {n_weeks} WEEK)
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
        WHERE DATE(fact_sales.created_at) = DATE_SUB('{DATE}', INTERVAL {n_weeks} WEEK)
      )
      SELECT
        current_day.store_type AS store_type,
        COALESCE(current_day.sales, 0) AS sales,
        COALESCE(previous_period_same_day.sales, 0) AS previous_sales,
        COALESCE(current_day.sales, 0) - COALESCE(previous_period_same_day.sales, 0) AS sales_difference,
        (SAFE_DIVIDE(COALESCE(current_day.sales, 0), NULLIF(COALESCE(previous_period_same_day.sales, 0), 0)) - 1) * 100 AS sales_percentage_variation,

        COALESCE(current_day.transactions, 0) AS transactions,
        COALESCE(previous_period_same_day.transactions, 0) AS previous_transactions,
        COALESCE(current_day.transactions, 0) - COALESCE(previous_period_same_day.transactions, 0) AS transactions_difference,
        (SAFE_DIVIDE(COALESCE(current_day.transactions, 0), NULLIF(COALESCE(previous_period_same_day.transactions, 0), 0)) - 1) * 100 AS transactions_percentage_variation,

        COALESCE(current_day.margin, 0) AS margin,
        COALESCE(previous_period_same_day.margin, 0) AS previous_margin,
        COALESCE(current_day.margin, 0) - COALESCE(previous_period_same_day.margin, 0) AS margin_difference,
        (SAFE_DIVIDE(COALESCE(current_day.margin, 0), NULLIF(COALESCE(previous_period_same_day.margin, 0), 0)) - 1) * 100 AS margin_percentage_variation,

        COALESCE(current_day.percentage_margin, 0) AS percentage_margin,
        COALESCE(previous_period_same_day.percentage_margin, 0) AS previous_percentage_margin,
        COALESCE(current_day.percentage_margin, 0) - COALESCE(previous_period_same_day.percentage_margin, 0) AS percentage_margin_difference,
        (SAFE_DIVIDE(COALESCE(current_day.percentage_margin, 0), NULLIF(COALESCE(previous_period_same_day.percentage_margin, 0), 0)) - 1) * 100 AS percentage_margin_percentage_variation,

        COALESCE(current_day.average_order_value, 0) AS order_value,
        COALESCE(previous_period_same_day.average_order_value, 0) AS previous_order_value,
        COALESCE(current_day.average_order_value, 0) - COALESCE(previous_period_same_day.average_order_value, 0) AS order_value_difference,
        (SAFE_DIVIDE(COALESCE(current_day.average_order_value, 0), NULLIF(COALESCE(previous_period_same_day.average_order_value, 0), 0)) - 1) * 100 AS order_value_percentage_variation,

        COALESCE(current_day.items_per_transaction, 0) AS items,
        COALESCE(previous_period_same_day.items_per_transaction, 0) AS previous_items,
        COALESCE(current_day.items_per_transaction, 0) - COALESCE(previous_period_same_day.items_per_transaction, 0) AS items_difference,
        (SAFE_DIVIDE(COALESCE(current_day.items_per_transaction, 0), NULLIF(COALESCE(previous_period_same_day.items_per_transaction, 0), 0)) - 1) * 100 AS items_percentage_variation

      FROM current_day
      LEFT JOIN previous_period_same_day
      ON current_day.store_type = previous_period_same_day.store_type;
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
      "comparing {DATE} versus the same weekday from {n_weeks} week(s) ago",
    "query": """
      WITH current_day AS 
      (
        SELECT
          SUM(sales_amount) AS sales,
          SUM(revenue) AS margin,
          SAFE_DIVIDE(SUM(revenue), NULLIF(SUM(sales_amount), 0)) * 100 AS percentage_margin,
          COUNT(DISTINCT ticket_id) AS transactions,
          SAFE_DIVIDE(SUM(sales_amount), NULLIF(COUNT(DISTINCT ticket_id), 0)) AS average_order_value,
          SAFE_DIVIDE(SUM(quantity), NULLIF(COUNT(DISTINCT ticket_id), 0)) AS items_per_transaction
        FROM fact_sales
        WHERE DATE(created_at) = '{DATE}'
      ),
      previous_period_same_day AS 
      (
        SELECT
          SUM(sales_amount) AS sales,
          SUM(revenue) AS margin,
          SAFE_DIVIDE(SUM(revenue), NULLIF(SUM(sales_amount), 0)) * 100 AS percentage_margin,
          COUNT(DISTINCT ticket_id) AS transactions,
          SAFE_DIVIDE(SUM(sales_amount), NULLIF(COUNT(DISTINCT ticket_id), 0)) AS average_order_value,
          SAFE_DIVIDE(SUM(quantity), NULLIF(COUNT(DISTINCT ticket_id), 0)) AS items_per_transaction
        FROM fact_sales
        WHERE DATE(created_at) = DATE_SUB('{DATE}', INTERVAL {n_weeks} WEEK )
      )
      SELECT
        COALESCE(current_day.sales, 0) AS sales,
        COALESCE(previous_period_same_day.sales, 0) AS previous_sales,
        COALESCE(current_day.sales, 0) - COALESCE(previous_period_same_day.sales, 0) AS sales_difference,
        (SAFE_DIVIDE(COALESCE(current_day.sales, 0), NULLIF(COALESCE(previous_period_same_day.sales, 0), 0)) - 1) * 100 AS sales_percentage_variation,

        COALESCE(current_day.transactions, 0) AS transactions,
        COALESCE(previous_period_same_day.transactions, 0) AS previous_transactions,
        COALESCE(current_day.transactions, 0) - COALESCE(previous_period_same_day.transactions, 0) AS transactions_difference,
        (SAFE_DIVIDE(COALESCE(current_day.transactions, 0), NULLIF(COALESCE(previous_period_same_day.transactions, 0), 0)) - 1) * 100 AS transactions_percentage_variation,

        COALESCE(current_day.margin, 0) AS margin,
        COALESCE(previous_period_same_day.margin, 0) AS previous_margin,
        COALESCE(current_day.margin, 0) - COALESCE(previous_period_same_day.margin, 0) AS margin_difference,
        (SAFE_DIVIDE(COALESCE(current_day.margin, 0), NULLIF(COALESCE(previous_period_same_day.margin, 0), 0)) - 1) * 100 AS margin_percentage_variation,

        COALESCE(current_day.percentage_margin, 0) AS percentage_margin,
        COALESCE(previous_period_same_day.percentage_margin, 0) AS previous_percentage_margin,
        COALESCE(current_day.percentage_margin, 0) - COALESCE(previous_period_same_day.percentage_margin, 0) AS percentage_margin_difference,
        (SAFE_DIVIDE(COALESCE(current_day.percentage_margin, 0), NULLIF(COALESCE(previous_period_same_day.percentage_margin, 0), 0)) - 1) * 100 AS percentage_margin_percentage_variation,

        COALESCE(current_day.average_order_value, 0) AS order_value,
        COALESCE(previous_period_same_day.average_order_value, 0) AS previous_order_value,
        COALESCE(current_day.average_order_value, 0) - COALESCE(previous_period_same_day.average_order_value, 0) AS order_value_difference,
        (SAFE_DIVIDE(COALESCE(current_day.average_order_value, 0), NULLIF(COALESCE(previous_period_same_day.average_order_value, 0), 0)) - 1) * 100 AS order_value_percentage_variation,

        COALESCE(current_day.items_per_transaction, 0) AS items,
        COALESCE(previous_period_same_day.items_per_transaction, 0) AS previous_items,
        COALESCE(current_day.items_per_transaction, 0) - COALESCE(previous_period_same_day.items_per_transaction, 0) AS items_difference,
        (SAFE_DIVIDE(COALESCE(current_day.items_per_transaction, 0), NULLIF(COALESCE(previous_period_same_day.items_per_transaction, 0), 0)) - 1) * 100 AS items_percentage_variation

      FROM current_day, previous_period_same_day;
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
      "comparing {DATE} versus the {n_day_rolling_average}-day rolling average?",
    "query": """
      WITH current_day AS 
      (
        SELECT
          SUM(sales_amount) AS sales,
          SUM(revenue) AS margin,
          SAFE_DIVIDE(SUM(revenue), NULLIF(SUM(sales_amount), 0)) * 100 AS percentage_margin,
          COUNT(DISTINCT ticket_id) AS transactions,
          SAFE_DIVIDE(SUM(sales_amount), NULLIF(COUNT(DISTINCT ticket_id), 0)) AS average_order_value,
          SAFE_DIVIDE(SUM(quantity), NULLIF(COUNT(DISTINCT ticket_id), 0)) AS items_per_transaction
        FROM fact_sales
        WHERE DATE(created_at) = '{DATE}'
      ),
      rolling_average AS 
      (
        SELECT
          AVG(sales_amount_sum) AS avg_sales,
          AVG(margin_sum) AS avg_margin,
          AVG(percentage_margin_calc) AS avg_percentage_margin,
          AVG(transactions_count) AS avg_transactions,
          AVG(average_order_value_calc) AS avg_average_order_value,
          AVG(items_per_transaction_calc) AS avg_items_per_transaction
        FROM 
        (
          SELECT
            SUM(sales_amount) AS sales_amount_sum,
            SUM(revenue) AS margin_sum,
            SAFE_DIVIDE(SUM(revenue), NULLIF(SUM(sales_amount), 0)) AS percentage_margin_calc,
            COUNT(DISTINCT ticket_id) AS transactions_count,
            SAFE_DIVIDE(SUM(sales_amount), NULLIF(COUNT(DISTINCT ticket_id), 0)) AS average_order_value_calc,
            SAFE_DIVIDE(SUM(quantity), NULLIF(COUNT(DISTINCT ticket_id), 0)) AS items_per_transaction_calc
          FROM fact_sales
          WHERE created_at >= TIMESTAMP_SUB('{DATE}', INTERVAL {n_day_rolling_average} DAY)
            AND created_at < '{DATE}'
          GROUP BY DATE(created_at)
        ) AS daily_data
      )
      SELECT
        current_day.sales AS sales,
        rolling_average.avg_sales AS rolling_average_sales,
        COALESCE(current_day.sales, 0) - COALESCE(rolling_average.avg_sales, 0) AS sales_difference,
        (SAFE_DIVIDE(COALESCE(current_day.sales, 0), NULLIF(COALESCE(rolling_average.avg_sales, 0), 0)) - 1) * 100 AS sales_percentage_variation,

        current_day.transactions AS transactions,
        rolling_average.avg_transactions AS rolling_average_transactions,
        COALESCE(current_day.transactions, 0) - COALESCE(rolling_average.avg_transactions, 0) AS transactions_difference,
        (SAFE_DIVIDE(COALESCE(current_day.transactions, 0), NULLIF(COALESCE(rolling_average.avg_transactions, 0), 0)) - 1) * 100 AS transactions_percentage_variation,

        current_day.margin AS margin,
        rolling_average.avg_margin AS rolling_average_margin,
        COALESCE(current_day.margin, 0) - COALESCE(rolling_average.avg_margin, 0) AS margin_difference,
        (SAFE_DIVIDE(COALESCE(current_day.margin, 0), NULLIF(COALESCE(rolling_average.avg_margin, 0), 0)) - 1) * 100 AS margin_percentage_variation,

        current_day.percentage_margin AS percentage_margin,
        rolling_average.avg_percentage_margin AS rolling_average_percentage_margin,
        COALESCE(current_day.percentage_margin, 0) - COALESCE(rolling_average.avg_percentage_margin, 0) AS percentage_margin_difference,
        (SAFE_DIVIDE(COALESCE(current_day.percentage_margin, 0), NULLIF(COALESCE(rolling_average.avg_percentage_margin, 0), 0)) - 1) * 100 AS percentage_margin_percentage_variation,

        current_day.average_order_value AS order_value,
        rolling_average.avg_average_order_value AS rolling_average_order_value,
        COALESCE(current_day.average_order_value, 0) - COALESCE(rolling_average.avg_average_order_value, 0) AS order_value_difference,
        (SAFE_DIVIDE(COALESCE(current_day.average_order_value, 0), NULLIF(COALESCE(rolling_average.avg_average_order_value, 0), 0)) - 1) * 100 AS order_value_percentage_variation,

        current_day.items_per_transaction AS items,
        rolling_average.avg_items_per_transaction AS rolling_average_items,
        COALESCE(current_day.items_per_transaction, 0) - COALESCE(rolling_average.avg_items_per_transaction, 0) AS items_difference,
        (SAFE_DIVIDE(COALESCE(current_day.items_per_transaction, 0), NULLIF(COALESCE(rolling_average.avg_items_per_transaction, 0), 0)) - 1) * 100 AS items_percentage_variation

      FROM current_day, rolling_average;
    """
  },
  {
    "question":
      "What was our "
      "total sales, "
      "total margin ,"
      "percentage margin "
      "from {DATE} for the top {top_n_high_performance_stores} stores in high performance "
      "in terms of "
      "sales, "
      "margin and "
      "percentage margin",
    "query": """
      WITH ranked_stores AS 
      (
        SELECT
          ds.store_id,
          ds.store_name,
          SUM(fs.sales_amount) AS total_sales,
          SUM(fs.revenue) AS total_margin,
          SAFE_DIVIDE(SUM(fs.revenue), NULLIF(SUM(fs.sales_amount), 0)) * 100 AS percentage_margin,

          -- Rankings para cada métrica
          RANK() OVER (ORDER BY SUM(fs.sales_amount) DESC) AS rank_total_sales,
          RANK() OVER (ORDER BY SUM(fs.revenue) DESC) AS rank_total_margin,
          RANK() OVER (ORDER BY SAFE_DIVIDE(SUM(fs.revenue), NULLIF(SUM(fs.sales_amount), 0)) * 100 DESC) AS rank_percentage_margin

        FROM fact_sales fs
        JOIN dim_stores ds ON fs.store_id = ds.store_id
        WHERE DATE(fs.created_at) = '{DATE}'
        GROUP BY ds.store_id, ds.store_name
      )

      SELECT
        store_id,
        store_name,
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
      "from {DATE} for the top {top_n_low_performance_stores} stores in low performance "
      "in terms of "
      "sales, "
      "margin and "
      "percentage margin",
    "query": """
      WITH ranked_stores AS 
      (
        SELECT
          ds.store_id,
          ds.store_name,
          SUM(fs.sales_amount) AS total_sales,
          SUM(fs.revenue) AS total_margin,
          SAFE_DIVIDE(SUM(fs.revenue), NULLIF(SUM(fs.sales_amount), 0)) AS percentage_margin,
          RANK() OVER (ORDER BY SUM(fs.sales_amount) ASC) AS rank_total_sales,
          RANK() OVER (ORDER BY SUM(fs.revenue) ASC) AS rank_total_margin,
          RANK() OVER (ORDER BY SAFE_DIVIDE(SUM(fs.revenue), NULLIF(SUM(fs.sales_amount), 0)) ASC) AS rank_percentage_margin

        FROM fact_sales fs
        JOIN dim_stores ds ON fs.store_id = ds.store_id
        WHERE DATE(fs.created_at) = '{DATE}'
        GROUP BY ds.store_id, ds.store_name
      )

      SELECT
        store_id,
        store_name,
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
      "from {DATE} for the top {top_n_high_performance_stores} stores in high performance "
      "in terms of "
      "total transactions, "
      "average order value and "
      "items per transaction",
    "query": """
      WITH ranked_stores AS 
      (
        SELECT
          ds.store_id,
          ds.store_name,
          COALESCE(COUNT(DISTINCT fs.ticket_id), 0) AS total_transactions,
          COALESCE(SAFE_DIVIDE(SUM(fs.sales_amount), NULLIF(COUNT(DISTINCT fs.ticket_id), 0)), 0) AS average_order_value,
          COALESCE(SAFE_DIVIDE(SUM(fs.quantity), NULLIF(COUNT(DISTINCT fs.ticket_id), 0)), 0) AS items_per_transaction,

          RANK() OVER (ORDER BY COUNT(DISTINCT fs.ticket_id) DESC) AS rank_total_transactions,
          RANK() OVER (ORDER BY SAFE_DIVIDE(SUM(fs.sales_amount), NULLIF(COUNT(DISTINCT fs.ticket_id), 0)) DESC) AS rank_average_order_value,
          RANK() OVER (ORDER BY SAFE_DIVIDE(SUM(fs.quantity), NULLIF(COUNT(DISTINCT fs.ticket_id), 0)) DESC) AS rank_items_per_transaction

        FROM fact_sales fs
        JOIN dim_stores ds ON fs.store_id = ds.store_id
        WHERE DATE(fs.created_at) = '{DATE}'
        GROUP BY ds.store_id, ds.store_name
      )

      SELECT
        store_id,
        store_name,
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
      "from {DATE} for the top {top_n_low_performance_stores} stores in low performance "
      "in terms of "
      "total transactions, "
      "average order value and "
      "items per transaction",
    "query": """
      WITH ranked_stores AS 
      (
        SELECT
          ds.store_id,
          ds.store_name,
          COUNT(DISTINCT fs.ticket_id) AS total_transactions,
          COALESCE(SAFE_DIVIDE(SUM(fs.sales_amount), NULLIF(COUNT(DISTINCT fs.ticket_id), 0)), 0) AS average_order_value,
          COALESCE(SAFE_DIVIDE(SUM(fs.quantity), NULLIF(COUNT(DISTINCT fs.ticket_id), 0)), 0) AS items_per_transaction,

          RANK() OVER (ORDER BY COUNT(DISTINCT fs.ticket_id) ASC) AS rank_total_transactions,
          RANK() OVER (ORDER BY COALESCE(SAFE_DIVIDE(SUM(fs.sales_amount), NULLIF(COUNT(DISTINCT fs.ticket_id), 0)), 0) ASC) AS rank_average_order_value,
          RANK() OVER (ORDER BY COALESCE(SAFE_DIVIDE(SUM(fs.quantity), NULLIF(COUNT(DISTINCT fs.ticket_id), 0)), 0) ASC) AS rank_items_per_transaction

        FROM fact_sales fs
        JOIN dim_stores ds ON fs.store_id = ds.store_id
        WHERE DATE(fs.created_at) = '{DATE}'
        GROUP BY ds.store_id, ds.store_name
      )

      SELECT
        store_id,
        store_name,
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
      "from {DATE} for the top {top_n_high_performance_categories} categories in high performance "
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
        WHERE DATE(fs.created_at) = '{DATE}'
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
      "from {DATE} for the top {top_n_low_performance_categories} categories in low performance "
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
        WHERE DATE(fs.created_at) = '{DATE}'
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
      "from {DATE} for the top {top_n_high_performance_items} products in high performance "
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
        WHERE DATE(fs.created_at) = '{DATE}'
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
      "from {DATE} for the top {top_n_low_performance_items} products in low performance "
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
        WHERE DATE(fs.created_at) = '{DATE}'
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
      "percentage margin, "
      "total_transactions, "
      "average_order_value and "
      "items_per_transaction "
      "from {DATE} for all stores",
    "query": """
      SELECT
        ds.store_id,
        ds.store_name,
        COALESCE(SUM(sales_amount), 0) AS total_sales,
        COALESCE(SUM(revenue), 0) AS total_margin,
        SAFE_DIVIDE(COALESCE(SUM(revenue), 0), NULLIF(SUM(sales_amount), 0)) * 100 AS percentage_margin,
        COUNT(DISTINCT ticket_id) AS total_transactions,
        SAFE_DIVIDE(COALESCE(SUM(sales_amount), 0), NULLIF(COUNT(DISTINCT ticket_id), 0)) AS average_order_value,
        SAFE_DIVIDE(COALESCE(SUM(quantity), 0), NULLIF(COUNT(DISTINCT ticket_id), 0)) AS items_per_transaction
      FROM fact_sales fs
      JOIN dim_stores ds ON fs.store_id = ds.store_id
      WHERE DATE(fs.created_at) = '{DATE}'
      GROUP BY ds.store_id, ds.store_name
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
      "from {DATE} for all categories",
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
      WHERE DATE(fs.created_at) = '{DATE}'
      GROUP BY dc.category_id, dc.category_name
      LIMIT 20
    """
  },

  {
    "question": 
      "what was our "
      "total number of items sold, "
      "total number of items sold last day, "
      "total number of items sold last 30 days, "
      "total number of items sold month to date, "
      "total number of items sold month to date ratio with last year, "
      "total number of items sold year to date, "
      "total number of items sold year to date ratio with last year "
      "from {DATE}?",
    "query": """
      SELECT 
        items, 
        last_day, 
        last_30_days, 
        mtd, 
        mtd_ratio_with_last_year, 
        ytd, 
        ytd_ratio_with_last_year
      FROM agg_items_kpis
      WHERE date = '{DATE}'
    """
  },
  {
    "question": 
      "what was our "
      "sales, "
      "sales last day, "
      "sales last 30 days, "
      "sales month to date, "
      "sales month to date ratio with last year, "
      "sales year to date, "
      "sales year to date ratio with last year "
      "from {DATE}?",
    "query": """
      SELECT 
        sales, 
        last_day, 
        last_30_days, 
        mtd, 
        mtd_ratio_with_last_year, 
        ytd, 
        ytd_ratio_with_last_year
      FROM agg_sales_kpis
      WHERE date = '{DATE}'
    """
  },
  {
    "question": 
      "what was our "
      "total number of tickets, "
      "total number of tickets last day, "
      "total number of tickets last 30 days, "
      "total number of tickets month to date, "
      "total number of tickets month to date ratio with last year, "
      "total number of tickets year to date, "
      "total number of tickets year to date ratio with last year "
      "from {DATE}?",
    "query": """
      SELECT 
        tickets, 
        last_day, 
        last_30_days, 
        mtd, 
        mtd_ratio_with_last_year, 
        ytd, 
        ytd_ratio_with_last_year
      FROM agg_tickets_kpis
      WHERE date = '{DATE}'
    """
  },

  {
    "question":
      "What was our "
      "total sales amount current year, "
      "net margin current year, "
      "revenue current year, "
      "discount current year, "
      "brute margin current year, "
      "boxes sold current year, "
      "total sales amount last year, "
      "net margin last year, "
      "revenue last year, "
      "discount last year, "
      "brute margin last year, "
      "boxes sold last year, "
      "percentage of variation of total sales of the current year vs last year, "
      "Percentage of variation of boxes sold of the current year vs last year, "
      "Percentage of variation of margin of the current year vs last year "
      "for category?",
    "query": """
        SELECT 
            COALESCE(category_name, '') AS category_name,
            COALESCE(total_sales_amount_current_year, 0) AS total_sales_amount_current_year,
            COALESCE(net_margin_current_year, 0) AS net_margin_current_year,
            COALESCE(revenue_current_year, 0) AS revenue_current_year,
            COALESCE(discount_current_year, 0) AS discount_current_year,
            COALESCE(brute_margin_current_year, 0) AS brute_margin_current_year,
            COALESCE(boxes_current_year, 0) AS boxes_current_year,
            COALESCE(total_sales_amount_last_year, 0) AS total_sales_amount_last_year,
            COALESCE(net_margin_last_year, 0) AS net_margin_last_year,
            COALESCE(revenue_last_year, 0) AS revenue_last_year,
            COALESCE(discount_last_year, 0) AS discount_last_year,
            COALESCE(brute_margin_last_year, 0) AS brute_margin_last_year,
            COALESCE(boxes_last_year, 0) AS boxes_last_year,
            COALESCE(total_sales_variation, 0) AS total_sales_variation,
            COALESCE(boxes_variation, 0) AS boxes_variation,
            COALESCE(margin_variation, 0) AS margin_variation,
        FROM agg_category_sales_comparison_current_vs_last_year
        LIMIT 20
    """
  },
  {
    "question":
      "What was our "
      "total sales amount current year, "
      "net margin current year, "
      "brute margin current year, "
      "total sales amount last year, "
      "net margin last year, "
      "brute margin last year, "
      "percentage of variation of total sales of the current year vs last year"
      "difference of total sales of the current year vs last year"
      "for category with sales decline?",
    "query": """
      SELECT
        COALESCE(category_name, '') AS category_name,
        COALESCE(total_sales_amount_current_year, 0) AS total_sales_amount_current_year,
        COALESCE(net_margin_current_year, 0) AS net_margin_current_year,
        COALESCE(brute_margin_current_year, 0) AS brute_margin_current_year,
        COALESCE(total_sales_amount_last_year, 0) AS total_sales_amount_last_year,
        COALESCE(net_margin_last_year, 0) AS net_margin_last_year,
        COALESCE(brute_margin_last_year, 0) AS brute_margin_last_year,
        COALESCE(percentage, 0) AS percentage,
        COALESCE(difference, 0) AS difference
      FROM agg_category_sales_decline_current_vs_last_year
      LIMIT 20
    """
  },
  {
    "question":
      "What was our "
      "total sales without service payments last month, "
      "total sales of service payments last month, "
      "daily avg sales amount without service payments last month, "
      "daily avg sales amount of service payments last month, "
      "total sales without service payments current month, "
      "total sales of service payments current month, "
      "daily avg sales amount without service payments current month, "
      "daily avg sales amount of service payments current month, "
      "percentage of variation of daily avg sales amount without the payments of services of the current month vs last month "
      "for store?",
    "query": """
      SELECT
        COALESCE(store_name, '') AS store_name,
        COALESCE(total_sales_without_service_payments_last_month, 0) AS total_sales_without_service_payments_last_month,
        COALESCE(total_service_payments_last_month, 0) AS total_service_payments_last_month,
        COALESCE(daily_avg_without_service_payments_last_month, 0) AS daily_avg_without_service_payments_last_month,
        COALESCE(daily_avg_service_payments_last_month, 0) AS daily_avg_service_payments_last_month,
        COALESCE(total_sales_without_service_payments_current_month, 0) AS total_sales_without_service_payments_current_month,
        COALESCE(total_service_payments_current_month, 0) AS total_service_payments_current_month,
        COALESCE(daily_avg_without_service_payments_current_month, 0) AS daily_avg_without_service_payments_current_month,
        COALESCE(daily_avg_service_payments_current_month, 0) AS daily_avg_service_payments_current_month,
        COALESCE(percentage_daily_avg_vs_last_month, 0) AS percentage_daily_avg_vs_last_month,
      FROM agg_store_sales_comparison_current_vs_last_month
      LIMIT 20
    """
  },
  {
    "question":
      "What was our "
      "total sales current year, "
      "total sales without service payments current year, "
      "total service payments current year, "
      "net margin current year, "
      "revenue current year, "
      "discount current year, "
      "brute margin current year, "
      "avg daily sales current year, "
      "total sales last year, "
      "total sales without service payments last year, "
      "total service payments last year, "
      "net margin last year, "
      "revenue last year, "
      "discount last year, "
      "brute margin last year, "
      "avg daily sales last year, "
      "percentage of variation of total sales of the current year vs last year, "
      "percentage of variation of the margin of the current year vs last year "
      "for store?",
    "query": """
      SELECT
        COALESCE(store_name, '') AS store_name,
        COALESCE(total_sales_current_year, 0) AS total_sales_current_year,
        COALESCE(total_sales_without_service_payments_current_year, 0) AS total_sales_without_service_payments_current_year,
        COALESCE(total_service_payments_current_year, 0) AS total_service_payments_current_year,
        COALESCE(net_margin_current_year, 0) AS net_margin_current_year,
        COALESCE(revenue_current_year, 0) AS revenue_current_year,
        COALESCE(discount_current_year, 0) AS discount_current_year,
        COALESCE(brute_margin_current_year, 0) AS brute_margin_current_year,
        COALESCE(avg_daily_sales_current_year, 0) AS avg_daily_sales_current_year,
        COALESCE(total_sales_last_year, 0) AS total_sales_last_year,
        COALESCE(total_sales_without_service_payments_last_year, 0) AS total_sales_without_service_payments_last_year,
        COALESCE(total_service_payments_last_year, 0) AS total_service_payments_last_year,
        COALESCE(net_margin_last_year, 0) AS net_margin_last_year,
        COALESCE(revenue_last_year, 0) AS revenue_last_year,
        COALESCE(discount_last_year, 0) AS discount_last_year,
        COALESCE(brute_margin_last_year, 0) AS brute_margin_last_year,
        COALESCE(avg_daily_sales_last_year, 0) AS avg_daily_sales_last_year,
        COALESCE(total_sales_variation, 0) AS total_sales_variation,
        COALESCE(margin_variation, 0) AS margin_variation,
      FROM agg_store_sales_comparison_current_vs_last_year
      LIMIT 20
    """
  },
  {
    "question":
      "What was our "
      "total sales amount current year, "
      "net margin current year, "
      "brute margin current year, "
      "total sales amount last year, "
      "net margin last year, "
      "brute margin last year, "
      "percentage of variation of total sales of the current year vs last year"
      "difference of total sales of the current year vs last year"
      "for store with sales decline?",
    "query": """
      SELECT
        COALESCE(store_name, '') AS store_name,
        COALESCE(total_sales_amount_current_year, 0) AS total_sales_amount_current_year,
        COALESCE(net_margin_current_year, 0) AS net_margin_current_year,
        COALESCE(brute_margin_current_year, 0) AS brute_margin_current_year,
        COALESCE(total_sales_amount_last_year, 0) AS total_sales_amount_last_year,
        COALESCE(net_margin_last_year, 0) AS net_margin_last_year,
        COALESCE(brute_margin_last_year, 0) AS brute_margin_last_year,
        COALESCE(percentage, 0) AS percentage,
        COALESCE(difference, 0) AS difference
      FROM agg_store_sales_decline_current_vs_last_year
      LIMIT 20
    """
  },
  {
    "question":
      "What was our "
      "total sales, "
      "total revenue, "
      "margin "
      "of the top 50 items of the current month?",
    "query": """
      SELECT
        COALESCE(item_name, '') AS item_name,
        COALESCE(total_sales, 0) AS total_sales,
        COALESCE(total_revenue, 0) AS total_revenue,
        COALESCE(margin, 0) AS margin,
      FROM agg_top_50_items_sales_current_month
    """
  }
]

def get_default_questions(default_questions=default_questions):
  return default_questions
