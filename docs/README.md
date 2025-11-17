These is the official documentation for TeleDM -- A solution for situations where you just can't leave the tab in focus for a large file to get through

## Links

- [Configuration](./Configuration.md)
- [Usage Guide](./Usage.md)
- [FAQ](./FAQ.md)
- [Troubleshooting](./TroubleShooting.md)
- [Development](./development.md)


## Security Considerations

- **API Credentials**
	- Telegram **Doesn't let you revoke or delete your api credentials**, so make sure you NEVER EVER REVEAL your credentials ANYWHERE
- **Session Data**: 
	- Stored locally in a .sessioin file, keep secure or someone might be able to log in as you
- **Log Files**: May contain sensitive info, secure appropriately

## Performance Tips

- **Concurrent Downloads**: 
	- Balance between speed and system resources
- **Chunk Size**: 
	- Larger chunks for better speed, smaller for stability