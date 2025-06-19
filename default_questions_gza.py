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
        WHERE DATE(fs.created_at) = '{DATE}'
        GROUP BY ds.store_id, ds.store_name, ds.city
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
      "from {DATE} for the top {top_n_low_performance_stores} stores in low performance "
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
        WHERE DATE(fs.created_at) = '{DATE}'
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
      "from {DATE} for the top {top_n_high_performance_stores} stores in high performance "
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
        WHERE DATE(fs.created_at) = '{DATE}'
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
      "from {DATE} for the top {top_n_low_performance_stores} stores in low performance "
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
        WHERE DATE(fs.created_at) = '{DATE}'
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
      "percentage margin and "
      "total units sold "
      "from {DATE} for the top {top_n_high_performance_vendors} vendors in high performance "
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
        WHERE DATE(fs.created_at) = '{DATE}'
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
      "from {DATE} for the top {top_n_low_performance_vendors} vendors in low performance "
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
        WHERE DATE(fs.created_at) = '{DATE}'
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
      "from {DATE} for city?",
    "query": """
      SELECT
        ds.city,
        SUM(fs.sales_amount) AS total_sales,
        SUM(fs.revenue) AS total_margin,
        SAFE_DIVIDE(SUM(fs.revenue), NULLIF(SUM(fs.sales_amount), 0)) * 100 AS percentage_margin,
      FROM fact_sales fs
      JOIN dim_stores ds ON fs.store_id = ds.store_id
      WHERE DATE(fs.created_at) = '{DATE}'
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
      "from {DATE} for all stores and in which city is each store located?",
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
      WHERE DATE(fs.created_at) = '{DATE}'
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
      "from {DATE} for all categories ",
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
      "avg ticket amount, "
      "avg ticket amount last day, "
      "avg ticket amount last 30 days, "
      "avg ticket amount month to date, "
      "avg ticket amount month to date ratio with last year, "
      "avg ticket amount year to date, "
      "avg ticket amount year to date ratio with last year "
      "from {DATE}?",
    "query": """
      SELECT 
        avg_ticket_amount, 
        last_day, 
        last_30_days, 
        mtd, 
        mtd_ratio_with_last_year, 
        ytd, 
        ytd_ratio_with_last_year
      FROM agg_avg_ticket_amount_kpis
      WHERE date = '{DATE}'
    """
  },
  {
    "question":
      "what was our "
      "cost, "
      "cost last day, "
      "cost last 30 days, "
      "cost month to date, "
      "cost month to date ratio with last year, "
      "cost year to date, "
      "cost year to date ratio with last year "
      "from {DATE}?",
    "query": """
      SELECT 
        cost, 
        last_day, 
        last_30_days, 
        mtd, 
        mtd_ratio_with_last_year, 
        ytd, 
        ytd_ratio_with_last_year
      FROM agg_cost_kpis
      WHERE date = '{DATE}'
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
      "what was our "
      "sales revenue last day, "
      "sales revenue this week, "
      "sales revenue last week, "
      "sales revenue last 7 days, "
      "sales revenue month to date, "
      "sales revenue last 30 days, "
      "sales revenue last month, "
      "sales revenue year to date, "
      "sales revenue last year, "
      "sales revenue all time.",
    "query": """
      SELECT 
        yesterday,
        this_week,
        last_week,
        last_7_days,
        month_to_date,
        last_30_days,
        last_month,
        year_to_date,
        last_year,
        all_time
      FROM agg_kpi_daily_mv
      WHERE metric = 'Sales Revenue'
    """
  },
  {
    "question":
      "what was our "
      "quantity sold last day, "
      "quantity sold this week, "
      "quantity sold last week, "
      "quantity sold last 7 days, "
      "quantity sold month to date, "
      "quantity sold last 30 days, "
      "quantity sold last month, "
      "quantity sold year to date, "
      "quantity sold last year, "
      "quantity sold all time.",
    "query": """
      SELECT 
        yesterday,
        this_week,
        last_week,
        last_7_days,
        month_to_date,
        last_30_days,
        last_month,
        year_to_date,
        last_year,
        all_time
      FROM agg_kpi_daily_mv
      WHERE metric = 'Quantity'
    """
  },
  {
    "question":
      "what was our "
      "discount rate last day, "
      "discount rate this week, "
      "discount rate last week, "
      "discount rate last 7 days, "
      "discount rate month to date, "
      "discount rate last 30 days, "
      "discount rate last month, "
      "discount rate year to date, "
      "discount rate last year, "
      "discount rate all time.",
    "query": """
      SELECT 
        yesterday,
        this_week,
        last_week,
        last_7_days,
        month_to_date,
        last_30_days,
        last_month,
        year_to_date,
        last_year,
        all_time
      FROM agg_kpi_daily_mv
      WHERE metric = 'Discount Rate'
    """
  },
  {
    "question":
      "what was our "
      "margin last day, "
      "margin this week, "
      "margin last week, "
      "margin last 7 days, "
      "margin month to date, "
      "margin last 30 days, "
      "margin last month, "
      "margin year to date, "
      "margin last year, "
      "margin all time.",
    "query": """
      SELECT 
        yesterday,
        this_week,
        last_week,
        last_7_days,
        month_to_date,
        last_30_days,
        last_month,
        year_to_date,
        last_year,
        all_time
      FROM agg_kpi_daily_mv
      WHERE metric = 'Margin'
    """
  },
  {
    "question":
      "what was our "
      "avg ticket value last day, "
      "avg ticket value this week, "
      "avg ticket value last week, "
      "avg ticket value last 7 days, "
      "avg ticket value month to date, "
      "avg ticket value last 30 days, "
      "avg ticket value last month, "
      "avg ticket value year to date, "
      "avg ticket value last year, "
      "avg ticket value all time.",
    "query": """
      SELECT 
        yesterday,
        this_week,
        last_week,
        last_7_days,
        month_to_date,
        last_30_days,
        last_month,
        year_to_date,
        last_year,
        all_time
      FROM agg_kpi_daily_mv
      WHERE metric = 'Average Ticket Value'
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
      "total sales without service payments current year, "
      "total service payments current year, "
      "number of tickets current year, "
      "boxes sold current year, "
      "brute margin current year, "
      "net margin current year, "
      "total sales without service payments last year, "
      "total service payments last year, "
      "number of tickets last year, "
      "boxes sold last year, "
      "brute margin last year, "
      "net margin last year, "
      "percentage of variation of brute margin of the current year vs last year, "
      "percentage of variation of discount margin of the current year vs last year, "
      "percentage of variation of the number of tickets of the current year vs last year, "
      "percentage of variation of boxes sold of the current year vs last year, "
      "percentage of variation of total sales without the payments of services of the current year vs last year "
      "for {DATE}?",
    "query": """
      SELECT
        COALESCE(day, 0) AS day,
        COALESCE(total_sales_without_service_payments_current_year, 0) AS total_sales_without_service_payments_current_year,
        COALESCE(total_service_payments_current_year, 0) AS total_service_payments_current_year,
        COALESCE(num_tickets_current_year, 0) AS num_tickets_current_year,
        COALESCE(boxes_current_year, 0) AS boxes_current_year,
        COALESCE(brute_margin_current_year, 0) AS brute_margin_current_year,
        COALESCE(net_margin_current_year, 0) AS net_margin_current_year,
        COALESCE(total_sales_without_service_payments_last_year, 0) AS total_sales_without_service_payments_last_year,
        COALESCE(total_service_payments_last_year, 0) AS total_service_payments_last_year,
        COALESCE(num_tickets_last_year, 0) AS num_tickets_last_year,
        COALESCE(boxes_last_year, 0) AS boxes_last_year,
        COALESCE(brute_margin_last_year, 0) AS brute_margin_last_year,
        COALESCE(net_margin_last_year, 0) AS net_margin_last_year,
        COALESCE(brute_margin_variation, 0) AS brute_margin_variation,
        COALESCE(discount_margin_variation, 0) AS discount_margin_variation,
        COALESCE(num_tickets_variation, 0) AS num_tickets_variation,
        COALESCE(boxes_variation, 0) AS boxes_variation,
        COALESCE(total_sales_without_service_payments_variation, 0) AS total_sales_without_service_payments_variation,
      FROM agg_daily_sales_comparison_current_vs_last_year
      WHERE day = EXTRACT(DAY FROM DATE('{DATE}'))
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
      "from {DATE}?",
    "query": """
      WITH forecast AS 
      (
        SELECT 
          forecast_value, 
          confidence_interval_lower_bound AS lower_bound, 
          confidence_interval_upper_bound AS upper_bound 
        FROM 
          ML.FORECAST(MODEL modelo_arima_dia, STRUCT(30 AS horizon)) 
        WHERE 
          forecast_timestamp = '{DATE}'
      ), 
      actual AS 
      (
        SELECT 
          SUM(sales_amount) AS total_sales 
        FROM 
          fact_sales 
        WHERE 
          EXTRACT(DATE FROM created_at) = '{DATE}'
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
      "from {DATE}?",
    "query": """
      WITH forecast AS 
      (
        SELECT 
          forecast_value, 
          confidence_interval_lower_bound AS lower_bound, 
          confidence_interval_upper_bound AS upper_bound 
        FROM 
          ML.FORECAST(MODEL modelo_arima_dia_cost, STRUCT(30 AS horizon)) 
        WHERE 
          forecast_timestamp = '{DATE}'
      ), 
      actual AS 
      (
        SELECT 
          SUM(cost) AS total_cost 
        FROM 
          fact_sales 
        WHERE 
          EXTRACT(DATE FROM created_at) = '{DATE}'
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
      "from {DATE}?",
    "query": """
      WITH forecast AS 
      (
        WITH sales AS 
        (
          SELECT * 
          FROM ML.FORECAST(MODEL modelo_arima_dia, STRUCT(30 AS horizon, 0.99 AS confidence_level))
          WHERE 
            forecast_timestamp = '{DATE}'
        ), 
        costs AS 
        (
          SELECT * 
          FROM ML.FORECAST(MODEL modelo_arima_dia_cost, STRUCT(30 AS horizon, 0.99 AS confidence_level))
          WHERE 
            forecast_timestamp = '{DATE}'
        ) 
        SELECT 
          s.forecast_timestamp, 
          s.forecast_value AS total_sales, 
          c.forecast_value AS total_cost, 
          (s.forecast_value - c.forecast_value) AS revenue, 
          (s.prediction_interval_lower_bound - c.prediction_interval_lower_bound) AS prediction_interval_lower_bound, 
          (s.prediction_interval_upper_bound - c.prediction_interval_upper_bound) AS prediction_interval_upper_bound 
        FROM sales s, costs c 
      ), 
      actual AS 
      (
        SELECT 
          SUM(revenue) AS revenue 
        FROM fact_sales 
        WHERE 
          EXTRACT(DATE FROM created_at) = '{DATE}'
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
      "from {DATE}?",
    "query": """
      WITH forecast AS 
      (
        WITH sales AS 
        (
          SELECT * 
          FROM ML.FORECAST(MODEL modelo_arima_dia, STRUCT(30 AS horizon, 0.99 AS confidence_level))
          WHERE 
            forecast_timestamp = '{DATE}'
        ), 
        costs AS 
        (
          SELECT * 
          FROM ML.FORECAST(MODEL modelo_arima_dia_cost, STRUCT(30 AS horizon, 0.99 AS confidence_level))
          WHERE 
            forecast_timestamp = '{DATE}'
        ) 
        SELECT 
          s.forecast_timestamp, 
          s.forecast_value AS total_sales, 
          c.forecast_value AS total_cost, 
          ((COALESCE(s.forecast_value, 0) - COALESCE(c.forecast_value, 0)) / NULLIF(s.forecast_value,0)) AS margen, 
          ((COALESCE(s.prediction_interval_lower_bound, 0) - COALESCE(c.prediction_interval_lower_bound, 0)) / NULLIF(s.prediction_interval_lower_bound, 0)) AS prediction_interval_lower_bound, 
          ((COALESCE(s.prediction_interval_upper_bound, 0) - COALESCE(c.prediction_interval_upper_bound, 0)) / NULLIF(s.prediction_interval_upper_bound, 0)) AS prediction_interval_upper_bound 
        FROM sales s 
        JOIN costs c ON s.forecast_timestamp = c.forecast_timestamp
      ), 
      actual AS 
      (
        SELECT 
          (SUM(revenue) / NULLIF(SUM(sales_amount), 0)) AS margen 
        FROM fact_sales 
        WHERE 
          EXTRACT(DATE FROM created_at) = '{DATE}'
      ) 
      SELECT 
        COALESCE(a.margen, 0) AS actual_margen, 
        COALESCE(f.margen, 0) AS margen_forecast,
        COALESCE(f.prediction_interval_lower_bound, 0) AS lower_bound, 
        COALESCE(f.prediction_interval_upper_bound, 0) AS upper_bound,
        (COALESCE(a.margen, 0) - COALESCE(f.margen, 0)) AS difference,
        COALESCE((((COALESCE(a.margen, 0) / NULLIF(f.margen, 0)) - 1) * 100), 0) AS percentage 
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
      "from {DATE} for category?",
    "query": """
      WITH forecast AS 
      (
        SELECT 
          category_name, 
          forecast_timestamp, 
          forecast_value, 
          confidence_interval_lower_bound AS lower_bound, 
          confidence_interval_upper_bound AS upper_bound 
        FROM ML.FORECAST(MODEL modelo_arima_dia_categories, STRUCT(30 AS horizon)) 
        WHERE 
        forecast_timestamp = '{DATE}'
      ), 
      actual AS 
      (
        SELECT 
          category_name, 
          SUM(sales_amount) AS total_sales 
        FROM fact_sales s 
        JOIN dim_categories c ON s.category_id = c.category_id 
        WHERE 
          EXTRACT(DATE FROM created_at) = '{DATE}'
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
      "from {DATE} for store?",
    "query": """
      WITH forecast AS 
      (
        SELECT 
          store_name,  
          forecast_value, 
          confidence_interval_lower_bound AS lower_bound, 
          confidence_interval_upper_bound AS upper_bound 
        FROM ML.FORECAST(MODEL modelo_arima_dia_stores, STRUCT(30 AS horizon)) 
        WHERE 
        forecast_timestamp = '{DATE}'
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
      "for the next day?",
    "query": """
      SELECT 
        COALESCE(forecast_value, 0) AS total_sales, 
        COALESCE(confidence_interval_lower_bound, 0) AS lower_bound, 
        COALESCE(confidence_interval_upper_bound, 0) AS upper_bound 
      FROM 
        ML.FORECAST(MODEL modelo_arima_dia, STRUCT(30 AS horizon)) 
      WHERE 
        EXTRACT(DATE FROM forecast_timestamp) = DATE_ADD('{DATE}', INTERVAL 1 DAY)
    """
  },
  {
    "question":
      "What will be our "
      "total cost, "
      "lower bound, "
      "upper bound "
      "for the next day?",
    "query": """
      SELECT 
        COALESCE(forecast_value, 0) AS total_cost,
        COALESCE(confidence_interval_lower_bound, 0) AS lower_bound, 
        COALESCE(confidence_interval_upper_bound, 0) AS upper_bound 
      FROM 
        ML.FORECAST(MODEL modelo_arima_dia_cost, STRUCT(30 AS horizon)) 
      WHERE 
        EXTRACT(DATE FROM forecast_timestamp) = DATE_ADD('{DATE}', INTERVAL 1 DAY)
    """
  },
  {
    "question":
      "What will be our "
      "total revenue, "
      "lower bound, "
      "upper bound "
      "for the next day?",
    "query": """
      WITH sales AS 
      (
        SELECT * 
        FROM ML.FORECAST(MODEL modelo_arima_dia, STRUCT(30 AS horizon, 0.99 AS confidence_level))
        WHERE 
          EXTRACT(DATE FROM forecast_timestamp) = DATE_ADD('{DATE}', INTERVAL 1 DAY)
      ), 
      costs AS 
      (
        SELECT * 
        FROM ML.FORECAST(MODEL modelo_arima_dia_cost, STRUCT(30 AS horizon, 0.99 AS confidence_level))
        WHERE 
          EXTRACT(DATE FROM forecast_timestamp) = DATE_ADD('{DATE}', INTERVAL 1 DAY)
      ) 
      SELECT 
        (COALESCE(s.forecast_value, 0) - COALESCE(c.forecast_value, 0)) AS revenue, 
        (COALESCE(s.prediction_interval_lower_bound, 0) - COALESCE(c.prediction_interval_lower_bound, 0)) AS prediction_interval_lower_bound, 
        (COALESCE(s.prediction_interval_upper_bound, 0) - COALESCE(c.prediction_interval_upper_bound, 0)) AS prediction_interval_upper_bound 
      FROM sales s, costs c
    """
  },
  {
    "question":
      "What will be our "
      "margin, "
      "lower bound, "
      "upper bound "
      "for next day?",
    "query": """
      WITH sales AS 
      (
        SELECT * 
        FROM ML.FORECAST(MODEL modelo_arima_dia, STRUCT(60 AS horizon, 0.99 AS confidence_level))
        WHERE 
            EXTRACT(MONTH FROM forecast_timestamp) = EXTRACT(MONTH FROM DATE_ADD(DATE('{DATE}'), INTERVAL 1 DAY)) AND
            EXTRACT(YEAR FROM forecast_timestamp) = EXTRACT(YEAR FROM DATE_ADD(DATE('{DATE}'), INTERVAL 1 DAY))
      ), 
      costs AS 
      (
        SELECT * 
        FROM ML.FORECAST(MODEL modelo_arima_dia_cost, STRUCT(60 AS horizon, 0.99 AS confidence_level))
        WHERE 
            EXTRACT(MONTH FROM forecast_timestamp) = EXTRACT(MONTH FROM DATE_ADD(DATE('{DATE}'), INTERVAL 1 DAY)) AND
            EXTRACT(YEAR FROM forecast_timestamp) = EXTRACT(YEAR FROM DATE_ADD(DATE('{DATE}'), INTERVAL 1 DAY))
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
      "for the next day for category?",
    "query": """
      SELECT 
        COALESCE(category_name, '') AS category_name, 
        COALESCE(forecast_value, 0) AS total_sales,
        COALESCE(confidence_interval_lower_bound, 0) AS lower_bound, 
        COALESCE(confidence_interval_upper_bound, 0) AS upper_bound 
      FROM ML.FORECAST(MODEL modelo_arima_dia_categories, STRUCT(30 AS horizon)) 
      WHERE 
        EXTRACT(DATE FROM forecast_timestamp) = DATE_ADD('{DATE}', INTERVAL 1 DAY)
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
      "for the next day for store?",
    "query": """
      SELECT 
        COALESCE(store_name, '') AS store_name, 
        COALESCE(forecast_value, 0) AS total_sales, 
        COALESCE(confidence_interval_lower_bound, 0) AS lower_bound, 
        COALESCE(confidence_interval_upper_bound, 0) AS upper_bound 
      FROM ML.FORECAST(MODEL modelo_arima_dia_stores, STRUCT(30 AS horizon)) 
      WHERE 
        EXTRACT(DATE FROM forecast_timestamp) = DATE_ADD('{DATE}', INTERVAL 1 DAY)
      ORDER BY total_sales DESC
      LIMIT 20
    """
  },
]

def get_default_questions(default_questions=default_questions):
  return default_questions
