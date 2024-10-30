# Ensure administrator privileges
if (!([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]'Administrator')) {
    Write-Host "Restarting script with administrator privileges..." -ForegroundColor Yellow
    Start-Process PowerShell.exe -ArgumentList ("-NoProfile -ExecutionPolicy Bypass -File `"{0}`"" -f $PSCommandPath) -Verb RunAs
    exit	
}

$store = 'Cert:\LocalMachine\My'
$params = @{
	Type = 'Custom'
	Subject = 'CN=Microsoft Windows, O=Microsoft Corporation, L=Redmond, S=Washington, C=US'
	TextExtension = @(
		# Enhanced Key Usage
		'2.5.29.37={text}1.3.6.1.4.1.311.10.3.6',
		# Basic Constraints
		'2.5.29.19={text}false',
		# Subject Alternative Name
		'2.5.29.17={text}DirectoryName=SERIALNUMBER="229879+500176",OU=Microsoft Ireland Operations Limited'
	)
	KeyUsage = 'None'
	KeyAlgorithm = 'RSA'
	KeyLength = 2048
	NotAfter = (Get-Date).AddMonths(9999)
	CertStoreLocation = $store
}

# Create the certificate and store its thumbprint
$thumbprint = (New-SelfSignedCertificate @params).Thumbprint

# Check if certificate exists
if (Get-ChildItem -Path $store | Where-Object { $_.Thumbprint -eq $thumbprint }) {
    Write-Host "Certificate created with Thumbprint: $thumbprint" -ForegroundColor Green
} else {
    Write-Host "Failed to create certificate" -ForegroundColor Red
}

pause
