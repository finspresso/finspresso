<?php
$strJsonFileContents = file_get_contents("sql_credentials_test.json");
$sql_credentials = json_decode($strJsonFileContents, true);
$mysqli = new mysqli($sql_credentials["hostname"], $sql_credentials["user"], $sql_credentials["password"], $sql_credentials["db_name"], $sql_credentials["port"]);;
if($mysqli->connect_error) {
  exit('Could not connect');
}

$desired_category = $_GET['q'];
$sql = "SELECT $desired_category FROM inflation_lik WHERE year = 2019";
$stmt = $mysqli->prepare($sql);
$stmt->execute();
$stmt->store_result();
$stmt->bind_result($fetched_value);
$stmt->fetch();
$stmt->close();
echo "<table>";
echo "<tr>";
echo "<th>ID</th>";
echo "<td>" . $id . "</td>";
echo "<th>fetched Value</th>";
echo "<td>" . $fetched_value . "</td>";
echo "</tr>";
echo "</table>";
?>
