<?php 

    // print_r($_POST );
// Отправка письма 
// mail('ziharevi187@gmail.com', 'From WebSite', $_POST['message']);

$message = "Вам пришло новое сообщение с сайта: <br><br>\n" .
           "<strong>Имя отправителя: </strong>" . strip_tags(trim($_POST['name']))  . "<br>\n" . 
           "<strong>Email отправителя: </strong>" . strip_tags(trim($_POST['email']))  . "<br>\n" . 
           "<strong>Сообщение:</strong> " . strip_tags(trim($_POST['message'])) . "<br>\n";

// echo $message;
$mailResult = mail('ziharevi187@gmail.com', 'From WebSite', $message);
if ($mailResult) {
    header('location: thankyou.html');
} else {
    header('location: error.html');
}


