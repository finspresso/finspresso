<?php
define('DB_HOST', 'localhost');
define('DB_USERNAME', 'root');
define('DB_PASSWORD', '');
define('DB_NAME', 'dummy');
$mysqli = new mysqli(DB_HOST, DB_USERNAME, DB_PASSWORD, DB_NAME);
//$mysqli = new mysqli("servername", "username", "password", "dbname");
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
