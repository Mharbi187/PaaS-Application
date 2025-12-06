from python_terraform import Terraform
from pathlib import Path

terraform_exe = str(Path('./terraform_bin/terraform.exe').absolute())
tf = Terraform(working_dir='./terraform', terraform_bin_path=terraform_exe)
tf.workspace('select', 'frontend_ecommerce')
result = tf.destroy(auto_approve=True)
print(result)
