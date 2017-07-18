#include <sox.h>
#include <stdlib.h>

extern int go_flow_shim_impl(void* fn, sox_bool all_done);

sox_effect_handler_t const * go_sox_effect_fn_shim(sox_effect_fn_t const* fn);
int go_sox_flow_shim(sox_bool all_done, void *client_data);
sox_flow_effects_callback go_sox_get_flow_shim();

sox_effect_handler_t const * go_sox_effect_fn_shim(sox_effect_fn_t const* fn) {
	return (*fn)();
}

int go_sox_flow_shim(sox_bool all_done, void *client_data) {
	return go_flow_shim_impl(client_data, all_done);
}

sox_flow_effects_callback go_sox_get_flow_shim() {
	  return &go_sox_flow_shim;
}
