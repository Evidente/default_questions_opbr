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
      "for the week that ends on {DATE}",
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
        WHERE DATE(created_at) BETWEEN DATE_SUB('{DATE}', INTERVAL 6 DAY) AND '{DATE}'
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
      "comparing the week that ends on {DATE} versus the week from {n_weeks} week(s) ago, "
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
        current_week AS 
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
          WHERE DATE(created_at) BETWEEN DATE_SUB('{DATE}', INTERVAL 6 DAY) AND '{DATE}'
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
          WHERE DATE(created_at) BETWEEN DATE_SUB('{DATE}', INTERVAL 6 DAY) AND '{DATE}'
        ),
        previous_period_same_week AS 
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
          WHERE DATE(created_at) BETWEEN DATE_SUB(DATE_SUB('{DATE}', INTERVAL 6 DAY), INTERVAL {n_weeks} WEEK) AND DATE_SUB('{DATE}', INTERVAL {n_weeks} WEEK)
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
          WHERE DATE(created_at) BETWEEN DATE_SUB(DATE_SUB('{DATE}', INTERVAL 6 DAY), INTERVAL {n_weeks} WEEK) AND DATE_SUB('{DATE}', INTERVAL {n_weeks} WEEK)
        )
        SELECT
          current_week.store_type AS store_type,
          COALESCE(current_week.sales, 0) AS sales,
          COALESCE(previous_period_same_week.sales, 0) AS previous_sales,
          COALESCE(current_week.sales, 0) - COALESCE(previous_period_same_week.sales, 0) AS sales_difference,
          (SAFE_DIVIDE(COALESCE(current_week.sales, 0), NULLIF(COALESCE(previous_period_same_week.sales, 0), 0)) - 1) * 100 AS sales_percentage_variation,

          COALESCE(current_week.transactions, 0) AS transactions,
          COALESCE(previous_period_same_week.transactions, 0) AS previous_transactions,
          COALESCE(current_week.transactions, 0) - COALESCE(previous_period_same_week.transactions, 0) AS transactions_difference,
          (SAFE_DIVIDE(COALESCE(current_week.transactions, 0), NULLIF(COALESCE(previous_period_same_week.transactions, 0), 0)) - 1) * 100 AS transactions_percentage_variation,

          COALESCE(current_week.margin, 0) AS margin,
          COALESCE(previous_period_same_week.margin, 0) AS previous_margin,
          COALESCE(current_week.margin, 0) - COALESCE(previous_period_same_week.margin, 0) AS margin_difference,
          (SAFE_DIVIDE(COALESCE(current_week.margin, 0), NULLIF(COALESCE(previous_period_same_week.margin, 0), 0)) - 1) * 100 AS margin_percentage_variation,

          COALESCE(current_week.percentage_margin, 0) AS percentage_margin,
          COALESCE(previous_period_same_week.percentage_margin, 0) AS previous_percentage_margin,
          COALESCE(current_week.percentage_margin, 0) - COALESCE(previous_period_same_week.percentage_margin, 0) AS percentage_margin_difference,
          (SAFE_DIVIDE(COALESCE(current_week.percentage_margin, 0), NULLIF(COALESCE(previous_period_same_week.percentage_margin, 0), 0)) - 1) * 100 AS percentage_margin_percentage_variation,

          COALESCE(current_week.average_order_value, 0) AS order_value,
          COALESCE(previous_period_same_week.average_order_value, 0) AS previous_order_value,
          COALESCE(current_week.average_order_value, 0) - COALESCE(previous_period_same_week.average_order_value, 0) AS order_value_difference,
          (SAFE_DIVIDE(COALESCE(current_week.average_order_value, 0), NULLIF(COALESCE(previous_period_same_week.average_order_value, 0), 0)) - 1) * 100 AS order_value_percentage_variation,

          COALESCE(current_week.items_per_transaction, 0) AS items,
          COALESCE(previous_period_same_week.items_per_transaction, 0) AS previous_items,
          COALESCE(current_week.items_per_transaction, 0) - COALESCE(previous_period_same_week.items_per_transaction, 0) AS items_difference,
          (SAFE_DIVIDE(COALESCE(current_week.items_per_transaction, 0), NULLIF(COALESCE(previous_period_same_week.items_per_transaction, 0), 0)) - 1) * 100 AS items_percentage_variation

        FROM current_week
        LEFT JOIN previous_period_same_week
        ON current_week.store_type = previous_period_same_week.store_type;
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
      "comparing the week that ends on {DATE} versus the same week from {n_weeks} week(s) ago",
    "query": """
      WITH current_week AS 
      (
        SELECT
          SUM(sales_amount) AS sales,
          SUM(revenue) AS margin,
          SAFE_DIVIDE(SUM(revenue), NULLIF(SUM(sales_amount), 0)) * 100 AS percentage_margin,
          COUNT(DISTINCT ticket_id) AS transactions,
          SAFE_DIVIDE(SUM(sales_amount), NULLIF(COUNT(DISTINCT ticket_id), 0)) AS average_order_value,
          SAFE_DIVIDE(SUM(quantity), NULLIF(COUNT(DISTINCT ticket_id), 0)) AS items_per_transaction
        FROM fact_sales
        WHERE DATE(created_at) BETWEEN DATE_SUB('{DATE}', INTERVAL 6 DAY) AND '{DATE}'
      ),
      previous_period_same_week AS 
      (
        SELECT
          SUM(sales_amount) AS sales,
          SUM(revenue) AS margin,
          SAFE_DIVIDE(SUM(revenue), NULLIF(SUM(sales_amount), 0)) * 100 AS percentage_margin,
          COUNT(DISTINCT ticket_id) AS transactions,
          SAFE_DIVIDE(SUM(sales_amount), NULLIF(COUNT(DISTINCT ticket_id), 0)) AS average_order_value,
          SAFE_DIVIDE(SUM(quantity), NULLIF(COUNT(DISTINCT ticket_id), 0)) AS items_per_transaction
        FROM fact_sales
        WHERE DATE(created_at) BETWEEN DATE_SUB(DATE_SUB('{DATE}', INTERVAL 6 DAY), INTERVAL {n_weeks} WEEK) AND DATE_SUB('{DATE}', INTERVAL {n_weeks} WEEK)
      )
      SELECT
        COALESCE(current_week.sales, 0) AS sales,
        COALESCE(previous_period_same_week.sales, 0) AS previous_sales,
        COALESCE(current_week.sales, 0) - COALESCE(previous_period_same_week.sales, 0) AS sales_difference,
        (SAFE_DIVIDE(COALESCE(current_week.sales, 0), NULLIF(COALESCE(previous_period_same_week.sales, 0), 0)) - 1) * 100 AS sales_percentage_variation,

        COALESCE(current_week.transactions, 0) AS transactions,
        COALESCE(previous_period_same_week.transactions, 0) AS previous_transactions,
        COALESCE(current_week.transactions, 0) - COALESCE(previous_period_same_week.transactions, 0) AS transactions_difference,
        (SAFE_DIVIDE(COALESCE(current_week.transactions, 0), NULLIF(COALESCE(previous_period_same_week.transactions, 0), 0)) - 1) * 100 AS transactions_percentage_variation,

        COALESCE(current_week.margin, 0) AS margin,
        COALESCE(previous_period_same_week.margin, 0) AS previous_margin,
        COALESCE(current_week.margin, 0) - COALESCE(previous_period_same_week.margin, 0) AS margin_difference,
        (SAFE_DIVIDE(COALESCE(current_week.margin, 0), NULLIF(COALESCE(previous_period_same_week.margin, 0), 0)) - 1) * 100 AS margin_percentage_variation,

        COALESCE(current_week.percentage_margin, 0) AS percentage_margin,
        COALESCE(previous_period_same_week.percentage_margin, 0) AS previous_percentage_margin,
        COALESCE(current_week.percentage_margin, 0) - COALESCE(previous_period_same_week.percentage_margin, 0) AS percentage_margin_difference,
        (SAFE_DIVIDE(COALESCE(current_week.percentage_margin, 0), NULLIF(COALESCE(previous_period_same_week.percentage_margin, 0), 0)) - 1) * 100 AS percentage_margin_percentage_variation,

        COALESCE(current_week.average_order_value, 0) AS order_value,
        COALESCE(previous_period_same_week.average_order_value, 0) AS previous_order_value,
        COALESCE(current_week.average_order_value, 0) - COALESCE(previous_period_same_week.average_order_value, 0) AS order_value_difference,
        (SAFE_DIVIDE(COALESCE(current_week.average_order_value, 0), NULLIF(COALESCE(previous_period_same_week.average_order_value, 0), 0)) - 1) * 100 AS order_value_percentage_variation,

        COALESCE(current_week.items_per_transaction, 0) AS items,
        COALESCE(previous_period_same_week.items_per_transaction, 0) AS previous_items,
        COALESCE(current_week.items_per_transaction, 0) - COALESCE(previous_period_same_week.items_per_transaction, 0) AS items_difference,
        (SAFE_DIVIDE(COALESCE(current_week.items_per_transaction, 0), NULLIF(COALESCE(previous_period_same_week.items_per_transaction, 0), 0)) - 1) * 100 AS items_percentage_variation

      FROM current_week, previous_period_same_week;
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
      "comparing the week that ends on {DATE} versus the week from {n_day_rolling_average}-day rolling average?",
    "query": """
      WITH current_week AS 
      (
        SELECT
          SUM(sales_amount) AS sales,
          SUM(revenue) AS margin,
          SAFE_DIVIDE(SUM(revenue), NULLIF(SUM(sales_amount), 0)) * 100 AS percentage_margin,
          COUNT(DISTINCT ticket_id) AS transactions,
          SAFE_DIVIDE(SUM(sales_amount), NULLIF(COUNT(DISTINCT ticket_id), 0)) AS average_order_value,
          SAFE_DIVIDE(SUM(quantity), NULLIF(COUNT(DISTINCT ticket_id), 0)) AS items_per_transaction
        FROM fact_sales
        WHERE DATE(created_at) BETWEEN DATE_SUB('{DATE}', INTERVAL 6 DAY) AND '{DATE}'
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
          WHERE DATE(created_at) >= DATE_SUB('{DATE}', INTERVAL {n_day_rolling_average} DAY)
            AND DATE(created_at) < '{DATE}'
          GROUP BY EXTRACT(WEEK FROM DATE(created_at))
        ) AS weekly_data
      )
      SELECT
        current_week.sales AS sales,
        rolling_average.avg_sales AS rolling_average_sales,
        COALESCE(current_week.sales, 0) - COALESCE(rolling_average.avg_sales, 0) AS sales_difference,
        (SAFE_DIVIDE(COALESCE(current_week.sales, 0), NULLIF(COALESCE(rolling_average.avg_sales, 0), 0)) - 1) * 100 AS sales_percentage_variation,

        current_week.transactions AS transactions,
        rolling_average.avg_transactions AS rolling_average_transactions,
        COALESCE(current_week.transactions, 0) - COALESCE(rolling_average.avg_transactions, 0) AS transactions_difference,
        (SAFE_DIVIDE(COALESCE(current_week.transactions, 0), NULLIF(COALESCE(rolling_average.avg_transactions, 0), 0)) - 1) * 100 AS transactions_percentage_variation,

        current_week.margin AS margin,
        rolling_average.avg_margin AS rolling_average_margin,
        COALESCE(current_week.margin, 0) - COALESCE(rolling_average.avg_margin, 0) AS margin_difference,
        (SAFE_DIVIDE(COALESCE(current_week.margin, 0), NULLIF(COALESCE(rolling_average.avg_margin, 0), 0)) - 1) * 100 AS margin_percentage_variation,

        current_week.percentage_margin AS percentage_margin,
        rolling_average.avg_percentage_margin AS rolling_average_percentage_margin,
        COALESCE(current_week.percentage_margin, 0) - COALESCE(rolling_average.avg_percentage_margin, 0) AS percentage_margin_difference,
        (SAFE_DIVIDE(COALESCE(current_week.percentage_margin, 0), NULLIF(COALESCE(rolling_average.avg_percentage_margin, 0), 0)) - 1) * 100 AS percentage_margin_percentage_variation,

        current_week.average_order_value AS order_value,
        rolling_average.avg_average_order_value AS rolling_average_order_value,
        COALESCE(current_week.average_order_value, 0) - COALESCE(rolling_average.avg_average_order_value, 0) AS order_value_difference,
        (SAFE_DIVIDE(COALESCE(current_week.average_order_value, 0), NULLIF(COALESCE(rolling_average.avg_average_order_value, 0), 0)) - 1) * 100 AS order_value_percentage_variation,

        current_week.items_per_transaction AS items,
        rolling_average.avg_items_per_transaction AS rolling_average_items,
        COALESCE(current_week.items_per_transaction, 0) - COALESCE(rolling_average.avg_items_per_transaction, 0) AS items_difference,
        (SAFE_DIVIDE(COALESCE(current_week.items_per_transaction, 0), NULLIF(COALESCE(rolling_average.avg_items_per_transaction, 0), 0)) - 1) * 100 AS items_percentage_variation

      FROM current_week, rolling_average;
    """
  },
  {
    "question":
      "What was our "
      "total sales, "
      "total margin ,"
      "percentage margin "
      "for the week that ends on {DATE} for the top {top_n_high_performance_stores} stores in high performance "
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
        WHERE DATE(created_at) BETWEEN DATE_SUB('{DATE}', INTERVAL 6 DAY) AND '{DATE}'
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
      LIMIT {top_n_high_performance_stores}
    """
  },
  {
    "question":
      "What was our "
      "total sales, "
      "total margin ,"
      "percentage margin "
      "for the week that ends on {DATE} for the top {top_n_low_performance_stores} stores in low performance "
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
        WHERE DATE(created_at) BETWEEN DATE_SUB('{DATE}', INTERVAL 6 DAY) AND '{DATE}'
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
      LIMIT {top_n_low_performance_stores}
    """
  },
  {
    "question" :
      "What was our "
      "total transactions, "
      "average order value and "
      "items per transaction "
      "for the week that ends on {DATE} for the top {top_n_high_performance_stores} stores in high performance "
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
        WHERE DATE(created_at) BETWEEN DATE_SUB('{DATE}', INTERVAL 6 DAY) AND '{DATE}'
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
      LIMIT {top_n_high_performance_stores}
    """
  },
  {
    "question" :
      "What was our "
      "total transactions, "
      "average order value and "
      "items per transaction "
      "for the week that ends on {DATE} for the top {top_n_low_performance_stores} stores in low performance "
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
        WHERE DATE(created_at) BETWEEN DATE_SUB('{DATE}', INTERVAL 6 DAY) AND '{DATE}'
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
      LIMIT {top_n_low_performance_stores}
    """
  },
  {
    "question":
      "What was our "
      "total sales, "
      "total margin ,"
      "percentage margin, "
      "total units sold "
      "for the week that ends on {DATE} for the top {top_n_high_performance_categories} categories in high performance "
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
        WHERE DATE(created_at) BETWEEN DATE_SUB('{DATE}', INTERVAL 6 DAY) AND '{DATE}'
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
      LIMIT {top_n_high_performance_categories}
    """
  },
  {
    "question":
      "What was our "
      "total sales, "
      "total margin ,"
      "percentage margin, "
      "total units sold "
      "for the week that ends on {DATE} for the top {top_n_low_performance_categories} categories in low performance "
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
        WHERE DATE(created_at) BETWEEN DATE_SUB('{DATE}', INTERVAL 6 DAY) AND '{DATE}'
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
      LIMIT {top_n_low_performance_categories}
    """
  },
  {
    "question":
      "What was our "
      "total sales, "
      "total margin ,"
      "percentage margin and "
      "total units sold "
      "for the week that ends on {DATE} for the top {top_n_high_performance_items} products in high performance "
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
        WHERE DATE(created_at) BETWEEN DATE_SUB('{DATE}', INTERVAL 6 DAY) AND '{DATE}'
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
      LIMIT {top_n_high_performance_items}
    """
  },
  {
    "question":
      "What was our "
      "total sales, "
      "total margin ,"
      "percentage margin and "
      "total units sold "
      "for the week that ends on {DATE} for the top {top_n_low_performance_items} products in low performance "
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
        WHERE DATE(created_at) BETWEEN DATE_SUB('{DATE}', INTERVAL 6 DAY) AND '{DATE}'
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
      LIMIT {top_n_low_performance_items}
    """
  },
  {
    "question": 
      "What was our "
      "total sales, "
      "total margin ,"
      "percentage margin and "
      "total units sold "
      "for the week that ends on {DATE} for the top {top_n_high_performance_vendors} vendors in high performance "
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
        WHERE DATE(created_at) BETWEEN DATE_SUB('{DATE}', INTERVAL 6 DAY) AND '{DATE}'
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
      LIMIT {top_n_high_performance_vendors}
    """
  },
  {
    "question":
      "What was our "
      "total sales, "
      "total margin ,"
      "percentage margin and "
      "total units sold "
      "for the week that ends on {DATE} for the top {top_n_low_performance_vendors} vendors in low performance "
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
        WHERE DATE(created_at) BETWEEN DATE_SUB('{DATE}', INTERVAL 6 DAY) AND '{DATE}'
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
      LIMIT {top_n_low_performance_vendors}
    """
  },
  {
    "question":
      "What was our "
      "total sales, "
      "total margin ,"
      "percentage margin "
      "for the week that ends on {DATE} for city?",
    "query": """
      SELECT
        ds.city,
        SUM(fs.sales_amount) AS total_sales,
        SUM(fs.revenue) AS total_margin,
        SAFE_DIVIDE(SUM(fs.revenue), NULLIF(SUM(fs.sales_amount), 0)) * 100 AS percentage_margin,
      FROM fact_sales fs
      JOIN dim_stores ds ON fs.store_id = ds.store_id
      WHERE DATE(created_at) BETWEEN DATE_SUB('{DATE}', INTERVAL 6 DAY) AND '{DATE}'
      GROUP BY ds.city
      LIMIT 10
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
      "for the week that ends on {DATE}?",
    "query": """
      WITH forecast AS 
      (
        SELECT 
          SUM(forecast_value) AS forecast_value, 
          SUM(confidence_interval_lower_bound) AS lower_bound, 
          SUM(confidence_interval_upper_bound) AS upper_bound 
        FROM 
          ML.FORECAST(MODEL modelo_arima_dia, STRUCT(40 AS horizon)) 
        WHERE DATE(forecast_timestamp) BETWEEN DATE_SUB('{DATE}', INTERVAL 6 DAY) AND '{DATE}'
      ), 
      actual AS 
      (
        SELECT 
          SUM(sales_amount) AS total_sales 
        FROM 
          fact_sales 
        WHERE DATE(created_at) BETWEEN DATE_SUB('{DATE}', INTERVAL 6 DAY) AND '{DATE}'
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
      "for the week that ends on {DATE}?",
    "query": """
      WITH forecast AS 
      (
        SELECT 
          SUM(forecast_value) AS forecast_value, 
          SUM(confidence_interval_lower_bound) AS lower_bound, 
          SUM(confidence_interval_upper_bound) AS upper_bound 
        FROM 
          ML.FORECAST(MODEL modelo_arima_dia_cost, STRUCT(40 AS horizon)) 
        WHERE DATE(forecast_timestamp) BETWEEN DATE_SUB('{DATE}', INTERVAL 6 DAY) AND '{DATE}'
      ), 
      actual AS 
      (
        SELECT 
          SUM(cost) AS total_cost 
        FROM 
          fact_sales 
        WHERE DATE(created_at) BETWEEN DATE_SUB('{DATE}', INTERVAL 6 DAY) AND '{DATE}'
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
      "for the week that ends on {DATE}?",
    "query": """
      WITH forecast AS 
      (
        WITH sales AS 
        (
          SELECT * 
          FROM ML.FORECAST(MODEL modelo_arima_dia, STRUCT(30 AS horizon, 0.99 AS confidence_level))
          WHERE DATE(forecast_timestamp) BETWEEN DATE_SUB('{DATE}', INTERVAL 6 DAY) AND '{DATE}'
        ), 
        costs AS 
        (
          SELECT * 
          FROM ML.FORECAST(MODEL modelo_arima_dia_cost, STRUCT(30 AS horizon, 0.99 AS confidence_level))
          WHERE DATE(forecast_timestamp) BETWEEN DATE_SUB('{DATE}', INTERVAL 6 DAY) AND '{DATE}'
      
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
        WHERE DATE(created_at) BETWEEN DATE_SUB('{DATE}', INTERVAL 6 DAY) AND '{DATE}'
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
      "for the week that ends on {DATE}?",
    "query": """
      WITH forecast AS 
      (
        WITH sales AS 
        (
          SELECT * 
          FROM ML.FORECAST(MODEL modelo_arima_dia, STRUCT(30 AS horizon, 0.99 AS confidence_level))
          WHERE DATE(forecast_timestamp) BETWEEN DATE_SUB('{DATE}', INTERVAL 6 DAY) AND '{DATE}'
        ), 
        costs AS 
        (
          SELECT * 
          FROM ML.FORECAST(MODEL modelo_arima_dia_cost, STRUCT(30 AS horizon, 0.99 AS confidence_level))
          WHERE DATE(forecast_timestamp) BETWEEN DATE_SUB('{DATE}', INTERVAL 6 DAY) AND '{DATE}'
        ) 
        SELECT 
          SUM(s.forecast_value) AS total_sales, 
          SUM(c.forecast_value) AS total_cost,  
          (SUM(s.forecast_value) - SUM(c.forecast_value)) AS margin, 
          (SUM(s.prediction_interval_lower_bound) - SUM(c.prediction_interval_lower_bound)) AS prediction_interval_lower_bound, 
          (SUM(s.prediction_interval_upper_bound) - SUM(c.prediction_interval_upper_bound)) AS prediction_interval_upper_bound 
        FROM sales s, costs c
      ), 
      actual AS 
      (
        SELECT 
          SUM(margin) AS margin 
        FROM fact_sales 
        WHERE DATE(created_at) BETWEEN DATE_SUB('{DATE}', INTERVAL 6 DAY) AND '{DATE}'
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
      "for the week that ends on {DATE} for category?",
    "query": """
      WITH forecast AS 
      (
        SELECT 
          category_name, 
          SUM(forecast_value) AS forecast_value, 
          SUM(confidence_interval_lower_bound) AS lower_bound, 
          SUM(confidence_interval_upper_bound) AS upper_bound 
        FROM ML.FORECAST(MODEL modelo_arima_dia_categories, STRUCT(40 AS horizon)) 
        WHERE DATE(forecast_timestamp) BETWEEN DATE_SUB('{DATE}', INTERVAL 6 DAY) AND '{DATE}'
        GROUP BY category_name
      ), 
      actual AS 
      (
        SELECT 
          category_name, 
          SUM(sales_amount) AS total_sales 
        FROM fact_sales s 
        JOIN dim_categories c ON s.category_id = c.category_id 
        WHERE DATE(created_at) BETWEEN DATE_SUB('{DATE}', INTERVAL 6 DAY) AND '{DATE}'
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
      LIMIT 10
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
      "for the week that ends on {DATE} for store?",
    "query": """
      WITH forecast AS 
      (
        SELECT 
          store_name,  
          SUM(forecast_value) AS forecast_value, 
          SUM(confidence_interval_lower_bound) AS lower_bound, 
          SUM(confidence_interval_upper_bound) AS upper_bound 
        FROM ML.FORECAST(MODEL modelo_arima_dia_stores, STRUCT(40 AS horizon)) 
        WHERE DATE(forecast_timestamp) BETWEEN DATE_SUB('{DATE}', INTERVAL 6 DAY) AND '{DATE}'
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
      LIMIT 10
    """
  },
  {
    "question":
      "What will be our "
      "total sales, "
      "lower bound, "
      "upper bound "
      "for the next week?",
    "query": """
      SELECT 
        COALESCE(SUM(forecast_value), 0) AS total_sales, 
        COALESCE(SUM(confidence_interval_lower_bound), 0) AS lower_bound, 
        COALESCE(SUM(confidence_interval_upper_bound), 0) AS upper_bound 
      FROM 
        ML.FORECAST(MODEL modelo_arima_dia, STRUCT(40 AS horizon)) 
      WHERE DATE(forecast_timestamp) BETWEEN DATE_ADD('{DATE}', INTERVAL 1 DAY) AND DATE_ADD('{DATE}', INTERVAL 7 DAY)
    """
  },
  {
    "question":
      "What will be our "
      "total cost, "
      "lower bound, "
      "upper bound "
      "for the next week?",
    "query": """
      SELECT 
        COALESCE(SUM(forecast_value), 0) AS total_cost,
        COALESCE(SUM(confidence_interval_lower_bound), 0) AS lower_bound, 
        COALESCE(SUM(confidence_interval_upper_bound), 0) AS upper_bound 
      FROM 
        ML.FORECAST(MODEL modelo_arima_dia_cost, STRUCT(40 AS horizon)) 
        WHERE DATE(forecast_timestamp) BETWEEN DATE_ADD('{DATE}', INTERVAL 1 DAY) AND DATE_ADD('{DATE}', INTERVAL 7 DAY)
    """
  },
  {
    "question":
      "What will be our "
      "total revenue, "
      "lower bound, "
      "upper bound "
      "for the next week?",
    "query": """
      WITH sales AS 
      (
        SELECT * 
        FROM ML.FORECAST(MODEL modelo_arima_dia, STRUCT(30 AS horizon, 0.99 AS confidence_level))
        WHERE DATE(forecast_timestamp) BETWEEN DATE_ADD('{DATE}', INTERVAL 1 DAY) AND DATE_ADD('{DATE}', INTERVAL 7 DAY)
      ), 
      costs AS 
      (
        SELECT * 
        FROM ML.FORECAST(MODEL modelo_arima_dia_cost, STRUCT(30 AS horizon, 0.99 AS confidence_level))
        WHERE DATE(forecast_timestamp) BETWEEN DATE_ADD('{DATE}', INTERVAL 1 DAY) AND DATE_ADD('{DATE}', INTERVAL 7 DAY)
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
      "for the next week?",
    "query": """
      WITH sales AS 
      (
        SELECT * 
        FROM ML.FORECAST(MODEL modelo_arima_dia, STRUCT(30 AS horizon, 0.99 AS confidence_level))
        WHERE DATE(forecast_timestamp) BETWEEN DATE_ADD('{DATE}', INTERVAL 1 DAY) AND DATE_ADD('{DATE}', INTERVAL 7 DAY)
      ), 
      costs AS 
      (
        SELECT * 
        FROM ML.FORECAST(MODEL modelo_arima_dia_cost, STRUCT(30 AS horizon, 0.99 AS confidence_level))
        WHERE DATE(forecast_timestamp) BETWEEN DATE_ADD('{DATE}', INTERVAL 1 DAY) AND DATE_ADD('{DATE}', INTERVAL 7 DAY)
      ) 
      SELECT 
        (COALESCE(SUM(s.forecast_value), 0) - COALESCE(SUM(c.forecast_value), 0)) AS margin, 
        (COALESCE(SUM(s.prediction_interval_lower_bound), 0) - COALESCE(SUM(c.prediction_interval_lower_bound), 0)) AS prediction_interval_lower_bound, 
        (COALESCE(SUM(s.prediction_interval_upper_bound), 0) - COALESCE(SUM(c.prediction_interval_upper_bound), 0)) AS prediction_interval_upper_bound 
      FROM sales s, costs c
    """
  },
  {
    "question":
      "What will be our "
      "total sales, "
      "lower bound, "
      "upper bound "
      "for the next week for category?",
    "query": """
      SELECT 
        COALESCE(category_name, '') AS category_name, 
        COALESCE(SUM(forecast_value), 0) AS total_sales,
        COALESCE(SUM(confidence_interval_lower_bound), 0) AS lower_bound, 
        COALESCE(SUM(confidence_interval_upper_bound), 0) AS upper_bound 
      FROM ML.FORECAST(MODEL modelo_arima_dia_categories, STRUCT(40 AS horizon)) 
      WHERE DATE(forecast_timestamp) BETWEEN DATE_ADD('{DATE}', INTERVAL 1 DAY) AND DATE_ADD('{DATE}', INTERVAL 7 DAY)
      GROUP BY category_name
      ORDER BY total_sales DESC
      LIMIT 10
    """
  },
  {
    "question":
      "What will be our "
      "total sales, "
      "lower bound, "
      "upper bound "
      "for the next week for store?",
    "query": """
      SELECT 
        COALESCE(store_name, '') AS store_name, 
        COALESCE(SUM(forecast_value), 0) AS total_sales,
        COALESCE(SUM(confidence_interval_lower_bound), 0) AS lower_bound, 
        COALESCE(SUM(confidence_interval_upper_bound), 0) AS upper_bound 
      FROM ML.FORECAST(MODEL modelo_arima_dia_stores, STRUCT(40 AS horizon)) 
      WHERE DATE(forecast_timestamp) BETWEEN DATE_ADD('{DATE}', INTERVAL 1 DAY) AND DATE_ADD('{DATE}', INTERVAL 7 DAY)
      GROUP BY store_name
      ORDER BY total_sales DESC
      LIMIT 10
    """
  },

  {
    "question":
      "What was our "
      "inventory turnover ratio, "
      "for the week that ends on {DATE} for the top {top_n_high_performance_stores} stores in high performance.",
    "query": """
      WITH initial_inventory AS 
      (
        SELECT 
          st.store_id,
          st.store_name,
          SUM(total_value) AS initial_inventory 
        FROM 
          fact_inventory_snapshots sn 
        JOIN dim_stores st ON sn.store_id = st.store_id 
        WHERE 
          EXTRACT(DATE FROM sn.snapshot_date) = DATE_SUB(DATE('{DATE}'), INTERVAL 7 DAY)
        GROUP BY 
          st.store_id,
          st.store_name
      ), 
      final_inventory AS 
      (
        SELECT 
          st.store_id,
          st.store_name,
          SUM(total_value) AS final_inventory 
        FROM 
          fact_inventory_snapshots sn 
        JOIN dim_stores st ON sn.store_id = st.store_id 
        WHERE 
          EXTRACT(DATE FROM sn.snapshot_date) = '{DATE}'
        GROUP BY 
          st.store_id,
          st.store_name
      ), 
      c AS 
      (
        SELECT 
          st.store_id,
          st.store_name,
          SUM(total_cost) AS total_cost 
        FROM 
          fact_inventory_movements m 
        JOIN dim_stores st ON m.store_id = st.store_id 
        WHERE 
          EXTRACT(DATE FROM m.movement_date) BETWEEN DATE_SUB(DATE('{DATE}'), INTERVAL 6 DAY) AND '{DATE}'
        GROUP BY 
          st.store_id,
          st.store_name
      ) 
      SELECT 
        ii.store_id,
        ii.store_name,
        (COALESCE(c.total_cost, 0) / NULLIF(((ii.initial_inventory + fi.final_inventory) / 2), 0)) AS ratio 
      FROM initial_inventory ii
      JOIN final_inventory fi ON ii.store_id = fi.store_id AND ii.store_name = fi.store_name
      JOIN c ON ii.store_id = c.store_id AND ii.store_name = c.store_name
      ORDER BY ratio DESC
      LIMIT {top_n_high_performance_stores}
    """
  },
  {
    "question":
      "What was our "
      "inventory turnover ratio, "
      "for the week that ends on {DATE} for the top {top_n_low_performance_stores} stores in low performance.",
    "query": """
      WITH initial_inventory AS 
      (
        SELECT 
          st.store_id,
          st.store_name,
          SUM(total_value) AS initial_inventory 
        FROM 
          fact_inventory_snapshots sn 
        JOIN dim_stores st ON sn.store_id = st.store_id 
        WHERE 
          EXTRACT(DATE FROM sn.snapshot_date) = DATE_SUB(DATE('{DATE}'), INTERVAL 7 DAY)
        GROUP BY 
          st.store_id,
          st.store_name
      ), 
      final_inventory AS 
      (
        SELECT 
          st.store_id,
          st.store_name,
          SUM(total_value) AS final_inventory 
        FROM 
          fact_inventory_snapshots sn 
        JOIN dim_stores st ON sn.store_id = st.store_id 
        WHERE 
          EXTRACT(DATE FROM sn.snapshot_date) = '{DATE}'
        GROUP BY 
          st.store_id,
          st.store_name
      ), 
      c AS 
      (
        SELECT 
          st.store_id,
          st.store_name,
          SUM(total_cost) AS total_cost 
        FROM 
          fact_inventory_movements m 
        JOIN dim_stores st ON m.store_id = st.store_id 
        WHERE 
          EXTRACT(DATE FROM m.movement_date) BETWEEN DATE_SUB(DATE('{DATE}'), INTERVAL 6 DAY) AND '{DATE}'
        GROUP BY 
          st.store_id,
          st.store_name
      ) 
      SELECT 
        ii.store_id,
        ii.store_name,
        (COALESCE(c.total_cost, 0) / NULLIF(((ii.initial_inventory + fi.final_inventory) / 2), 0)) AS ratio 
      FROM initial_inventory ii
      JOIN final_inventory fi ON ii.store_id = fi.store_id AND ii.store_name = fi.store_name
      JOIN c ON ii.store_id = c.store_id AND ii.store_name = c.store_name
      ORDER BY ratio ASC
      LIMIT {top_n_low_performance_stores}
    """
  },
  {
    "question":
      "What was our "
      "inventory turnover ratio, "
      "for the week that ends on {DATE} for the top {top_n_high_performance_items} items in high performance.",
    "query": """
      WITH initial_inventory AS 
      (
        SELECT 
          i.item_id,
          i.item_name,
          SUM(total_value) AS initial_inventory 
        FROM 
          fact_inventory_snapshots sn 
        JOIN dim_items i ON sn.item_id = i.item_id
        WHERE 
          EXTRACT(DATE FROM sn.snapshot_date) = DATE_SUB(DATE('{DATE}'), INTERVAL 7 DAY)
        GROUP BY 
          i.item_id,
          i.item_name
      ), 
      final_inventory AS 
      (
        SELECT 
          i.item_id,
          i.item_name,
          SUM(total_value) AS final_inventory 
        FROM 
          fact_inventory_snapshots sn 
        JOIN dim_items i ON sn.item_id = i.item_id
        WHERE 
          EXTRACT(DATE FROM sn.snapshot_date) = '{DATE}'
        GROUP BY 
          i.item_id,
          i.item_name
      ), 
      c AS 
      (
        SELECT 
          i.item_id,
          i.item_name,
          SUM(total_cost) AS total_cost 
        FROM 
          fact_inventory_movements m 
        JOIN dim_items i ON m.item_id = i.item_id
        WHERE 
          EXTRACT(DATE FROM m.movement_date) BETWEEN DATE_SUB(DATE('{DATE}'), INTERVAL 6 DAY) AND '{DATE}'
        GROUP BY 
          i.item_id,
          i.item_name
      ) 
      SELECT 
        ii.item_id,
        ii.item_name,
        (COALESCE(c.total_cost, 0) / NULLIF(((ii.initial_inventory + fi.final_inventory) / 2), 0)) AS ratio 
      FROM initial_inventory ii
      JOIN final_inventory fi ON ii.item_id = fi.item_id AND ii.item_name = fi.item_name
      JOIN c ON ii.item_id = c.item_id AND ii.item_name = c.item_name
      ORDER BY ratio DESC
      LIMIT {top_n_high_performance_items}
    """
  },
  {
    "question":
      "What was our "
      "inventory turnover ratio, "
      "for the week that ends on {DATE} for the top {top_n_low_performance_items} items in low performance.",
    "query": """
      WITH initial_inventory AS 
      (
        SELECT 
          i.item_id,
          i.item_name,
          SUM(total_value) AS initial_inventory 
        FROM 
          fact_inventory_snapshots sn 
        JOIN dim_items i ON sn.item_id = i.item_id
        WHERE 
          EXTRACT(DATE FROM sn.snapshot_date) = DATE_SUB(DATE('{DATE}'), INTERVAL 7 DAY)
        GROUP BY 
          i.item_id,
          i.item_name
      ), 
      final_inventory AS 
      (
        SELECT 
          i.item_id,
          i.item_name,
          SUM(total_value) AS final_inventory 
        FROM 
          fact_inventory_snapshots sn 
        JOIN dim_items i ON sn.item_id = i.item_id
        WHERE 
          EXTRACT(DATE FROM sn.snapshot_date) = '{DATE}'
        GROUP BY 
          i.item_id,
          i.item_name
      ), 
      c AS 
      (
        SELECT 
          i.item_id,
          i.item_name,
          SUM(total_cost) AS total_cost 
        FROM 
          fact_inventory_movements m 
        JOIN dim_items i ON m.item_id = i.item_id
        WHERE 
          EXTRACT(DATE FROM m.movement_date) BETWEEN DATE_SUB(DATE('{DATE}'), INTERVAL 6 DAY) AND '{DATE}'
        GROUP BY 
          i.item_id,
          i.item_name
      ) 
      SELECT 
        ii.item_id,
        ii.item_name,
        (COALESCE(c.total_cost, 0) / NULLIF(((ii.initial_inventory + fi.final_inventory) / 2), 0)) AS ratio 
      FROM initial_inventory ii
      JOIN final_inventory fi ON ii.item_id = fi.item_id AND ii.item_name = fi.item_name
      JOIN c ON ii.item_id = c.item_id AND ii.item_name = c.item_name
      ORDER BY ratio ASC
      LIMIT {top_n_low_performance_items}
    """
  },
  {
    "question":
      "What was our "
      "inventory turnover ratio, "
      "for the week that ends on {DATE} for the top {top_n_high_performance_categories} categories in high performance.",
    "query": """
      WITH initial_inventory AS 
      (
        SELECT 
          c.category_id,
          c.category_name,
          SUM(total_value) AS initial_inventory 
        FROM 
          fact_inventory_snapshots sn 
        JOIN fact_sales fs ON sn.item_id = fs.item_id AND sn.store_id = fs.store_id
        JOIN dim_categories c ON fs.category_id = c.category_id
        WHERE 
          EXTRACT(DATE FROM sn.snapshot_date) = DATE_SUB(DATE('{DATE}'), INTERVAL 7 DAY)
        GROUP BY 
          c.category_id,
          c.category_name
      ), 
      final_inventory AS 
      (
        SELECT 
          c.category_id,
          c.category_name,
          SUM(total_value) AS final_inventory 
        FROM 
          fact_inventory_snapshots sn 
        JOIN fact_sales fs ON sn.item_id = fs.item_id AND sn.store_id = fs.store_id
        JOIN dim_categories c ON fs.category_id = c.category_id
        WHERE 
          EXTRACT(DATE FROM sn.snapshot_date) = '{DATE}'
        GROUP BY 
          c.category_id,
          c.category_name
      ), 
      c AS 
      (
        SELECT 
          c.category_id,
          c.category_name,
          SUM(total_cost) AS total_cost 
        FROM 
          fact_inventory_movements m 
        JOIN fact_sales fs ON m.item_id = fs.item_id AND m.store_id = fs.store_id
        JOIN dim_categories c ON fs.category_id = c.category_id
        WHERE 
          EXTRACT(DATE FROM m.movement_date) BETWEEN DATE_SUB(DATE('{DATE}'), INTERVAL 6 DAY) AND '{DATE}'
        GROUP BY 
          c.category_id,
          c.category_name
      ) 
      SELECT 
        ii.category_id,
        ii.category_name,
        (COALESCE(c.total_cost, 0) / NULLIF(((ii.initial_inventory + fi.final_inventory) / 2), 0)) AS ratio 
      FROM initial_inventory ii
      JOIN final_inventory fi ON ii.category_id = fi.category_id AND ii.category_name = fi.category_name
      JOIN c ON ii.category_id = c.category_id AND ii.category_name = c.category_name
      ORDER BY ratio DESC
      LIMIT {top_n_high_performance_categories}
    """
  },
  {
    "question":
      "What was our "
      "inventory turnover ratio, "
      "for the week that ends on {DATE} for the top {top_n_low_performance_categories} categories in low performance.",
    "query": """
      WITH initial_inventory AS 
      (
        SELECT 
          c.category_id,
          c.category_name,
          SUM(total_value) AS initial_inventory 
        FROM 
          fact_inventory_snapshots sn 
        JOIN fact_sales fs ON sn.item_id = fs.item_id AND sn.store_id = fs.store_id
        JOIN dim_categories c ON fs.category_id = c.category_id
        WHERE 
          EXTRACT(DATE FROM sn.snapshot_date) = DATE_SUB(DATE('{DATE}'), INTERVAL 7 DAY)
        GROUP BY 
          c.category_id,
          c.category_name
      ), 
      final_inventory AS 
      (
        SELECT 
          c.category_id,
          c.category_name,
          SUM(total_value) AS final_inventory 
        FROM 
          fact_inventory_snapshots sn 
        JOIN fact_sales fs ON sn.item_id = fs.item_id AND sn.store_id = fs.store_id
        JOIN dim_categories c ON fs.category_id = c.category_id
        WHERE 
          EXTRACT(DATE FROM sn.snapshot_date) = '{DATE}'
        GROUP BY 
          c.category_id,
          c.category_name
      ), 
      c AS 
      (
        SELECT 
          c.category_id,
          c.category_name,
          SUM(total_cost) AS total_cost 
        FROM 
          fact_inventory_movements m 
        JOIN fact_sales fs ON m.item_id = fs.item_id AND m.store_id = fs.store_id
        JOIN dim_categories c ON fs.category_id = c.category_id
        WHERE 
          EXTRACT(DATE FROM m.movement_date) BETWEEN DATE_SUB(DATE('{DATE}'), INTERVAL 6 DAY) AND '{DATE}'
        GROUP BY 
          c.category_id,
          c.category_name
      ) 
      SELECT 
        ii.category_id,
        ii.category_name,
        (COALESCE(c.total_cost, 0) / NULLIF(((ii.initial_inventory + fi.final_inventory) / 2), 0)) AS ratio 
      FROM initial_inventory ii
      JOIN final_inventory fi ON ii.category_id = fi.category_id AND ii.category_name = fi.category_name
      JOIN c ON ii.category_id = c.category_id AND ii.category_name = c.category_name
      ORDER BY ratio ASC
      LIMIT {top_n_low_performance_categories}
    """
  },

  {
    "question":
      "What was our "
      "actual inventary, "
      "avg quantity sold, "
      "days of inventory available "
      "for the week that ends on {DATE} for the top {top_n_high_performance_stores} stores with more inventory available.",
    "query": """
      WITH initial_inventory AS 
      (
        SELECT 
          st.store_id,
          st.store_name,
          SUM(quantity_on_hand) AS initial_inventory, 
          sn.snapshot_date AS day 
        FROM fact_inventory_snapshots sn 
        JOIN dim_stores st ON sn.store_id = st.store_id 
        WHERE 
          EXTRACT(DATE FROM sn.snapshot_date) = DATE_SUB(DATE('{DATE}'), INTERVAL 7 DAY)
        GROUP BY 
          st.store_id,
          st.store_name,
          sn.snapshot_date
      ), 
      final_inventory AS 
      (
        SELECT 
          st.store_id,
          st.store_name,
          SUM(quantity_on_hand) AS final_inventory, 
          sn.snapshot_date AS day 
        FROM fact_inventory_snapshots sn 
        JOIN dim_stores st ON sn.store_id = st.store_id 
        WHERE 
          EXTRACT(DATE FROM sn.snapshot_date) = '{DATE}'
        GROUP BY 
          st.store_id,
          st.store_name,
          sn.snapshot_date
      ), 
      total_sales AS 
      (
        SELECT 
          st.store_id,
          st.store_name,
          ABS(SUM(quantity)) AS total_quantity 
        FROM fact_inventory_movements m 
        JOIN dim_stores st ON m.store_id = st.store_id 
        WHERE 
          EXTRACT(DATE FROM m.movement_date) BETWEEN DATE_SUB(DATE('{DATE}'), INTERVAL 6 DAY) AND '{DATE}' AND 
          m.movement_type_id = 2
        GROUP BY 
          st.store_id,
          st.store_name
      ) 
      SELECT 
        fi.store_id,
        fi.store_name,
        fi.final_inventory, 
        (ts.total_quantity / TIMESTAMP_DIFF(fi.day, ii.day, DAY)) AS avg_quantity, 
        (fi.final_inventory / (ts.total_quantity / TIMESTAMP_DIFF(fi.day, ii.day, DAY))) AS inventary_days 
      FROM final_inventory fi
      JOIN initial_inventory ii ON fi.store_id = ii.store_id AND fi.store_name = ii.store_name
      JOIN total_sales ts ON fi.store_id = ts.store_id AND fi.store_name = ts.store_name
      ORDER BY inventary_days DESC
      LIMIT {top_n_high_performance_stores}
    """
  },
  {
    "question":
      "What was our "
      "actual inventary, "
      "avg quantity sold, "
      "days of inventory available "
      "for the week that ends on {DATE} for the top {top_n_low_performance_stores} stores with less inventory available.",
    "query": """
      WITH initial_inventory AS 
      (
        SELECT 
          st.store_id,
          st.store_name,
          SUM(quantity_on_hand) AS initial_inventory, 
          sn.snapshot_date AS day 
        FROM fact_inventory_snapshots sn 
        JOIN dim_stores st ON sn.store_id = st.store_id 
        WHERE 
          EXTRACT(DATE FROM sn.snapshot_date) = DATE_SUB(DATE('{DATE}'), INTERVAL 7 DAY)
        GROUP BY 
          st.store_id,
          st.store_name,
          sn.snapshot_date
      ), 
      final_inventory AS 
      (
        SELECT 
          st.store_id,
          st.store_name,
          SUM(quantity_on_hand) AS final_inventory, 
          sn.snapshot_date AS day 
        FROM fact_inventory_snapshots sn 
        JOIN dim_stores st ON sn.store_id = st.store_id 
        WHERE 
          EXTRACT(DATE FROM sn.snapshot_date) = '{DATE}'
        GROUP BY 
          st.store_id,
          st.store_name,
          sn.snapshot_date
      ), 
      total_sales AS 
      (
        SELECT 
          st.store_id,
          st.store_name,
          ABS(SUM(quantity)) AS total_quantity 
        FROM fact_inventory_movements m 
        JOIN dim_stores st ON m.store_id = st.store_id 
        WHERE 
          EXTRACT(DATE FROM m.movement_date) BETWEEN DATE_SUB(DATE('{DATE}'), INTERVAL 6 DAY) AND '{DATE}' AND 
          m.movement_type_id = 2
        GROUP BY 
          st.store_id,
          st.store_name
      ) 
      SELECT 
        fi.store_id,
        fi.store_name,
        fi.final_inventory, 
        (ts.total_quantity / TIMESTAMP_DIFF(fi.day, ii.day, DAY)) AS avg_quantity, 
        (fi.final_inventory / (ts.total_quantity / TIMESTAMP_DIFF(fi.day, ii.day, DAY))) AS inventary_days 
      FROM final_inventory fi
      JOIN initial_inventory ii ON fi.store_id = ii.store_id AND fi.store_name = ii.store_name
      JOIN total_sales ts ON fi.store_id = ts.store_id AND fi.store_name = ts.store_name
      ORDER BY inventary_days ASC
      LIMIT {top_n_low_performance_stores}
    """
  },
  {
    "question":
      "What was our "
      "actual inventary, "
      "avg quantity sold, "
      "days of inventory available "
      "for the week that ends on {DATE} for the top {top_n_high_performance_items} items with more inventory available.",
    "query": """
      WITH initial_inventory AS 
      (
        SELECT 
          i.item_id,
          i.item_name,
          SUM(quantity_on_hand) AS initial_inventory, 
          sn.snapshot_date AS day 
        FROM fact_inventory_snapshots sn 
        JOIN dim_items i ON sn.item_id = i.item_id
        WHERE 
          EXTRACT(DATE FROM sn.snapshot_date) = DATE_SUB(DATE('{DATE}'), INTERVAL 7 DAY)
        GROUP BY 
          i.item_id,
          i.item_name,
          sn.snapshot_date
      ), 
      final_inventory AS 
      (
        SELECT 
          i.item_id,
          i.item_name,
          SUM(quantity_on_hand) AS final_inventory, 
          sn.snapshot_date AS day 
        FROM fact_inventory_snapshots sn 
        JOIN dim_items i ON sn.item_id = i.item_id
        WHERE 
          EXTRACT(DATE FROM sn.snapshot_date) = '{DATE}'
        GROUP BY 
          i.item_id,
          i.item_name,
          sn.snapshot_date
      ), 
      total_sales AS 
      (
        SELECT 
          i.item_id,
          i.item_name,
          ABS(SUM(quantity)) AS total_quantity 
        FROM fact_inventory_movements m 
        JOIN dim_items i ON m.item_id = i.item_id 
        WHERE 
          EXTRACT(DATE FROM m.movement_date) BETWEEN DATE_SUB(DATE('{DATE}'), INTERVAL 6 DAY) AND '{DATE}' AND 
          m.movement_type_id = 2
        GROUP BY 
          i.item_id,
          i.item_name
      ) 
      SELECT 
        fi.item_id,
        fi.item_name,
        fi.final_inventory, 
        (ts.total_quantity / TIMESTAMP_DIFF(fi.day, ii.day, DAY)) AS avg_quantity, 
        (fi.final_inventory / (ts.total_quantity / TIMESTAMP_DIFF(fi.day, ii.day, DAY))) AS inventary_days 
      FROM final_inventory fi
      JOIN initial_inventory ii ON fi.item_id = ii.item_id AND fi.item_name = ii.item_name
      JOIN total_sales ts ON fi.item_id = ts.item_id AND fi.item_name = ts.item_name
      ORDER BY inventary_days DESC
      LIMIT {top_n_high_performance_items}
    """
  },
  {
    "question":
      "What was our "
      "actual inventary, "
      "avg quantity sold, "
      "days of inventory available "
      "for the week that ends on {DATE} for the top {top_n_low_performance_items} items with less inventory available.",
    "query": """
      WITH initial_inventory AS 
      (
        SELECT 
          i.item_id,
          i.item_name,
          SUM(quantity_on_hand) AS initial_inventory, 
          sn.snapshot_date AS day 
        FROM fact_inventory_snapshots sn 
        JOIN dim_items i ON sn.item_id = i.item_id
        WHERE 
          EXTRACT(DATE FROM sn.snapshot_date) = DATE_SUB(DATE('{DATE}'), INTERVAL 7 DAY)
        GROUP BY 
          i.item_id,
          i.item_name,
          sn.snapshot_date
      ), 
      final_inventory AS 
      (
        SELECT 
          i.item_id,
          i.item_name,
          SUM(quantity_on_hand) AS final_inventory, 
          sn.snapshot_date AS day 
        FROM fact_inventory_snapshots sn 
        JOIN dim_items i ON sn.item_id = i.item_id
        WHERE 
          EXTRACT(DATE FROM sn.snapshot_date) = '{DATE}'
        GROUP BY 
          i.item_id,
          i.item_name,
          sn.snapshot_date
      ), 
      total_sales AS 
      (
        SELECT 
          i.item_id,
          i.item_name,
          ABS(SUM(quantity)) AS total_quantity 
        FROM fact_inventory_movements m 
        JOIN dim_items i ON m.item_id = i.item_id 
        WHERE 
          EXTRACT(DATE FROM m.movement_date) BETWEEN DATE_SUB(DATE('{DATE}'), INTERVAL 6 DAY) AND '{DATE}' AND 
          m.movement_type_id = 2
        GROUP BY 
          i.item_id,
          i.item_name
      ) 
      SELECT 
        fi.item_id,
        fi.item_name,
        fi.final_inventory, 
        (ts.total_quantity / TIMESTAMP_DIFF(fi.day, ii.day, DAY)) AS avg_quantity, 
        (fi.final_inventory / (ts.total_quantity / TIMESTAMP_DIFF(fi.day, ii.day, DAY))) AS inventary_days 
      FROM final_inventory fi
      JOIN initial_inventory ii ON fi.item_id = ii.item_id AND fi.item_name = ii.item_name
      JOIN total_sales ts ON fi.item_id = ts.item_id AND fi.item_name = ts.item_name
      ORDER BY inventary_days ASC
      LIMIT {top_n_low_performance_items}
    """
  },
  {
    "question":
      "What was our "
      "actual inventary, "
      "avg quantity sold, "
      "days of inventory available "
      "for the week that ends on {DATE} for the top {top_n_high_performance_categories} categories with more inventory available.",
    "query": """
      WITH initial_inventory AS 
      (
        SELECT 
          c.category_id,
          c.category_name,
          SUM(quantity_on_hand) AS initial_inventory, 
          sn.snapshot_date AS day 
        FROM fact_inventory_snapshots sn 
        JOIN dim_items i ON sn.item_id = i.item_id
        JOIN fact_sales fs ON i.item_id = fs.item_id
        JOIN dim_categories c ON fs.category_id = c.category_id
        WHERE 
          EXTRACT(DATE FROM sn.snapshot_date) = DATE_SUB(DATE('{DATE}'), INTERVAL 7 DAY)
        GROUP BY 
          c.category_id,
          c.category_name,
          sn.snapshot_date
      ), 
      final_inventory AS 
      (
        SELECT 
          c.category_id,
          c.category_name,
          SUM(quantity_on_hand) AS final_inventory, 
          sn.snapshot_date AS day 
        FROM fact_inventory_snapshots sn 
        JOIN dim_items i ON sn.item_id = i.item_id
        JOIN fact_sales fs ON i.item_id = fs.item_id
        JOIN dim_categories c ON fs.category_id = c.category_id
        WHERE 
          EXTRACT(DATE FROM sn.snapshot_date) = '{DATE}'
        GROUP BY 
          c.category_id,
          c.category_name,
          sn.snapshot_date
      ), 
      total_sales AS 
      (
        SELECT 
          c.category_id,
          c.category_name,
          ABS(SUM(m.quantity)) AS total_quantity 
        FROM fact_inventory_movements m 
        JOIN dim_items i ON m.item_id = i.item_id 
        JOIN fact_sales fs ON i.item_id = fs.item_id
        JOIN dim_categories c ON fs.category_id = c.category_id
        WHERE 
          EXTRACT(DATE FROM m.movement_date) BETWEEN DATE_SUB(DATE('{DATE}'), INTERVAL 6 DAY) AND '{DATE}' AND 
          m.movement_type_id = 2
        GROUP BY 
          c.category_id,
          c.category_name
      ) 
      SELECT 
        fi.category_id,
        fi.category_name,
        fi.final_inventory, 
        (ts.total_quantity / TIMESTAMP_DIFF(fi.day, ii.day, DAY)) AS avg_quantity, 
        (fi.final_inventory / (ts.total_quantity / TIMESTAMP_DIFF(fi.day, ii.day, DAY))) AS inventary_days 
      FROM final_inventory fi
      JOIN initial_inventory ii ON fi.category_id = ii.category_id AND fi.category_name = ii.category_name
      JOIN total_sales ts ON fi.category_id = ts.category_id AND fi.category_name = ts.category_name
      ORDER BY inventary_days DESC
      LIMIT {top_n_high_performance_categories}
    """
  },
  {
    "question":
      "What was our "
      "actual inventary, "
      "avg quantity sold, "
      "days of inventory available "
      "for the week that ends on {DATE} for the top {top_n_low_performance_categories} categories with less inventory available.",
    "query": """
      WITH initial_inventory AS 
      (
        SELECT 
          c.category_id,
          c.category_name,
          SUM(quantity_on_hand) AS initial_inventory, 
          sn.snapshot_date AS day 
        FROM fact_inventory_snapshots sn 
        JOIN dim_items i ON sn.item_id = i.item_id
        JOIN fact_sales fs ON i.item_id = fs.item_id
        JOIN dim_categories c ON fs.category_id = c.category_id
        WHERE 
          EXTRACT(DATE FROM sn.snapshot_date) = DATE_SUB(DATE('{DATE}'), INTERVAL 7 DAY)
        GROUP BY 
          c.category_id,
          c.category_name,
          sn.snapshot_date
      ), 
      final_inventory AS 
      (
        SELECT 
          c.category_id,
          c.category_name,
          SUM(quantity_on_hand) AS final_inventory, 
          sn.snapshot_date AS day 
        FROM fact_inventory_snapshots sn 
        JOIN dim_items i ON sn.item_id = i.item_id
        JOIN fact_sales fs ON i.item_id = fs.item_id
        JOIN dim_categories c ON fs.category_id = c.category_id
        WHERE 
          EXTRACT(DATE FROM sn.snapshot_date) = '{DATE}'
        GROUP BY 
          c.category_id,
          c.category_name,
          sn.snapshot_date
      ), 
      total_sales AS 
      (
        SELECT 
          c.category_id,
          c.category_name,
          ABS(SUM(m.quantity)) AS total_quantity 
        FROM fact_inventory_movements m 
        JOIN dim_items i ON m.item_id = i.item_id 
        JOIN fact_sales fs ON i.item_id = fs.item_id
        JOIN dim_categories c ON fs.category_id = c.category_id
        WHERE 
          EXTRACT(DATE FROM m.movement_date) BETWEEN DATE_SUB(DATE('{DATE}'), INTERVAL 6 DAY) AND '{DATE}' AND 
          m.movement_type_id = 2
        GROUP BY 
          c.category_id,
          c.category_name
      ) 
      SELECT 
        fi.category_id,
        fi.category_name,
        fi.final_inventory, 
        (ts.total_quantity / TIMESTAMP_DIFF(fi.day, ii.day, DAY)) AS avg_quantity, 
        (fi.final_inventory / (ts.total_quantity / TIMESTAMP_DIFF(fi.day, ii.day, DAY))) AS inventary_days 
      FROM final_inventory fi
      JOIN initial_inventory ii ON fi.category_id = ii.category_id AND fi.category_name = ii.category_name
      JOIN total_sales ts ON fi.category_id = ts.category_id AND fi.category_name = ts.category_name
      ORDER BY inventary_days DESC
      LIMIT {top_n_low_performance_categories}
    """
  },
  {
    "question":
      "What was our "
      "last sale, "
      "days without sales "
      "for {DATE} for the top {top_n_high_performance_stores} stores with more days without sales.",
    "query": """
      SELECT 
        st.store_id,
        st.store_name,
        MAX(m.movement_date) AS last_sale,
        DATE_DIFF('{DATE}', EXTRACT(DATE FROM MAX(m.movement_date)), DAY) AS days_without_sales
      FROM fact_inventory_movements m
      JOIN dim_stores st ON m.store_id = st.store_id
      WHERE 
        m.movement_type_id = 2 AND
        EXTRACT(DATE FROM m.movement_date) <= '{DATE}'
      GROUP BY
        st.store_id,
        st.store_name
      HAVING days_without_sales >= 7
      ORDER BY days_without_sales DESC
      LIMIT {top_n_high_performance_stores}
    """
  },
  {
    "question":
      "What was our "
      "last sale, "
      "days without sales "
      "for {DATE} for the top {top_n_high_performance_items} items with more days without sales.",
    "query": """
      SELECT 
        i.item_id,
        i.item_name,
        MAX(m.movement_date) AS last_sale,
        DATE_DIFF('{DATE}', EXTRACT(DATE FROM MAX(m.movement_date)), DAY) AS days_without_sales
      FROM fact_inventory_movements m
      JOIN dim_items i ON m.item_id = i.item_id
      WHERE 
        m.movement_type_id = 2 AND
        EXTRACT(DATE FROM m.movement_date) <= '{DATE}'
      GROUP BY
        i.item_id,
        i.item_name
      HAVING days_without_sales >= 30
      ORDER BY days_without_sales DESC
      LIMIT {top_n_high_performance_items}
    """
  },
  {
    "question":
      "What was our "
      "last sale, "
      "days without sales "
      "for {DATE} for the top {top_n_high_performance_categories} categories with more days without sales.",
    "query": """
      SELECT 
        c.category_id,
        c.category_name,
        MAX(m.movement_date) AS last_sale,
        DATE_DIFF('{DATE}', EXTRACT(DATE FROM MAX(m.movement_date)), DAY) AS days_without_sales
      FROM fact_inventory_movements m
      JOIN fact_sales fs ON m.item_id = fs.item_id
      join dim_categories c ON fs.category_id = c. category_id
      WHERE 
        m.movement_type_id = 2 AND
        EXTRACT(DATE FROM m.movement_date) <= '{DATE}'
      GROUP BY
        c.category_id,
        c.category_name
      HAVING days_without_sales >= 7
      ORDER BY days_without_sales DESC
      LIMIT {top_n_high_performance_categories}
    """
  },
]

def get_default_questions(default_questions=default_questions):
  return default_questions
