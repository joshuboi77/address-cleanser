class AddressCleanser < Formula
  desc "Parse, validate, and format US addresses"
  homepage "https://github.com/joshuboi77/address-cleanser"
  url "https://github.com/joshuboi77/address-cleanser/releases/download/v1.0.0/address-cleanser-darwin-universal.zip"
  sha256 "PLACEHOLDER_SHA256"
  version "1.0.0"
  license "MIT"

  def install
    bin.install "address-cleanser-darwin-universal" => "address-cleanser"
  end

  test do
    assert_match "Address Cleanser", shell_output("#{bin}/address-cleanser --help")
  end
end
