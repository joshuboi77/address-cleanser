class AddressCleanser < Formula
  desc "Parse, validate, and format US addresses"
  homepage "https://github.com/joshuboi77/address-cleanser"
  version "1.0.16"

  on_macos do
    if Hardware::CPU.arm?
      url "https://github.com/joshuboi77/address-cleanser/releases/download/v1.0.16/address-cleanser-macos-arm64.zip"
      sha256 "c849c9d58509f482c1c40afa542351e277d1f72a66e5573a7c67bd0fc36330a6"
    else
      url "https://github.com/joshuboi77/address-cleanser/releases/download/v1.0.16/address-cleanser-macos-universal.zip"
      sha256 "6d42c36ac36c794c39d0206b252f3a0a1787315f768b08ea3ee5857779890023"
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

