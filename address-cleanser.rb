class AddressCleanser < Formula
  desc "Parse, validate, and format US addresses"
  homepage "https://github.com/joshuboi77/address-cleanser"
  version "1.0.15"

  on_macos do
    if Hardware::CPU.arm?
      url "https://github.com/joshuboi77/address-cleanser/releases/download/v1.0.15/address-cleanser-macos-arm64.zip"
      sha256 "8bd0261decebec7d36ffdf8fd712d706921be36203f20a9fbcb19b4998a7d860"
    else
      url "https://github.com/joshuboi77/address-cleanser/releases/download/v1.0.15/address-cleanser-macos-universal.zip"
      sha256 "31d22922098f2a0662e14784ac44b569be8e7f48efcd0690fd72c1eca16557ee"
    end
  end

  def install
    bin.install "address-cleanser"
  end

  test do
    output = shell_output("#{bin}/address-cleanser --help")
    assert_match "Usage:", output
  end
end

