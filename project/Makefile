default: tmp.ll

%.ll: %.c
	clang -S -emit-llvm $<

%.ll: bench/%.bril cbril
	bril2json < $< | ./cbril > $@

%: %.ll
	clang $< -o $@
