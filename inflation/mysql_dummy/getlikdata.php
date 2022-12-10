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
$query = sprintf("SELECT id, health, year FROM inflation_lik");
//$query = "SELECT $desired_categoryi, year FROM inflation_lik";
//execute query
$result = $mysqli->query($query);
echo "<table>";
echo "<tr>";
  echo "<th> ID </th>";
  echo "<th> Value </th>";
  echo "<th> Year </th>";
echo "</tr>";
$data = array();
foreach ($result as $row) {
	$data[] = $row;
  echo "<tr>";
    echo "<td>" . $row["id"] . "</td>";
    echo "<td>" . $row["health"] . "</td>";
    echo "<td>" . $row["year"] . "</td>";
  echo "</tr>";
}
echo "</table>";

//free memory associated with result
$result->close();

//close connection
$mysqli->close();
?>
