import pytest
from pyspark.sql import SparkSession

pytestmark = pytest.mark.integration


def test_local_spark_session_executes_dataframe_job(spark: SparkSession) -> None:
    rows = spark.createDataFrame([(1,), (2,), (3,)], ["value"])

    assert rows.groupBy().sum("value").first()[0] == 6
