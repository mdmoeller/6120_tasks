default: linkedlist point

%.ll: %.c
	clang -S -emit-llvm $<

%.ll: %.bril brilc
	bril2json < $< | ./brilc > $@

%.ll: bench/%.bril brilc
	bril2json < $< | ./brilc > $@

%: %.ll
	clang $< -o $@
