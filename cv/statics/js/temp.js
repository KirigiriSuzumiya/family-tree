function changepic() {
 $("#prompt3").css("display", "none");
 var reads = new FileReader();
 f = document.getElementById('file').files[0];
 reads.readAsDataURL(f);
 reads.onload = function(e) {
 document.getElementById('img3').src = this.result;
 $("#img3").css("display", "block");
 };
}