for dir in /tmp/ansible/scripts/*/; do
    dirname=$(basename "$dir")
    tar -czf "/tmp/ansible/scripts/${dirname}.tar.gz" -C "/tmp/ansible/scripts" "$dirname"
    rm -rf "$dir"
done