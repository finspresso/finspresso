<?php
header('Content-Type: application/json');
// ini_set("log_errors", 1);
// ini_set("error_log", "/tmp/php-error.log");
require_once "db_credentials.php";
$mysqli = new mysqli($DBhostname, $DBusername, $DBpassword, $DBname, $DBport);
if($mysqli->connect_error) {
  exit('Could not connect');
}

$product_id = $_GET['q'];
$query = sprintf("SELECT $product_id, `Date` FROM `mbudget_prices` ORDER BY Date");
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
