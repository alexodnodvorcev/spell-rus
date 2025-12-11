.PHONY: mainta

mainta:
	cat ./dicts/iu7.txt | sort -u | sponge >./dicts/iu7.txt