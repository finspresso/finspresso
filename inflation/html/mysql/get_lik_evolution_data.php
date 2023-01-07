<?php
header('Content-Type: application/json');
$strJsonFileContents = file_get_contents("sql_credentials.json");
$sql_credentials = json_decode($strJsonFileContents, true);
$mysqli = new mysqli($sql_credentials["hostname"], $sql_credentials["user"], $sql_credentials["password"], $sql_credentials["db_name"], $sql_credentials["port"]);
if($mysqli->connect_error) {
  exit('Could not connect');
}

$desired_category = $_GET['q'];
$query = sprintf("SELECT $desired_category, Date FROM lik_evolution ORDER BY Date");
$result = $mysqli->query($query);
//loop through the returned data
$data = array();
foreach ($result as $row) {
	$data[] = $row;
}

//free memory associated with result
$result->close();

//close connection
$mysqli->close();
print json_encode($data);
?>
