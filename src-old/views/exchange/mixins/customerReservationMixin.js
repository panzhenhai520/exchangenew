// Shared mixin to manage AMLO reservation pre-check workflow across exchange flows.
// Ensures customer ID changes trigger reservation status lookup and guards transactions
// when pending or rejected reservations exist.

export default {
  data() {
    return {
      reservationStatus: null,
      disableExchange: false,
      reservationCheckTimer: null,
      reservationCheckLoading: false,
      reservationCheckError: null,
    };
  },

  watch: {
    customerId: {
      handler(newValue) {
        if (this.reservationCheckTimer) {
          clearTimeout(this.reservationCheckTimer);
          this.reservationCheckTimer = null;
        }

        const trimmed = (newValue || '').trim();
        if (!trimmed) {
          this._resetReservationState();
          return;
        }

        // Debounce reservation lookup to avoid excess API traffic while typing.
        this.reservationCheckTimer = setTimeout(() => {
          this._performReservationCheck(trimmed);
        }, 400);
      },
      immediate: false,
    },
  },

  mounted() {
    const initialId = (this.customerId || '').trim();
    if (initialId) {
      this._performReservationCheck(initialId);
    }
  },

  beforeUnmount() {
    if (this.reservationCheckTimer) {
      clearTimeout(this.reservationCheckTimer);
    }
  },

  methods: {
    async _performReservationCheck(customerId) {
      if (!this.$api) {
        // Fallback: component using this mixin must provide $api.
        return;
      }

      this.reservationCheckLoading = true;
      this.reservationCheckError = null;

      try {
        const response = await this.$api.get('/amlo/check-customer-reservation', {
          params: { customer_id: customerId },
        });

        const hasReservation = response?.data?.has_reservation;
        const reservation = hasReservation ? response.data : null;
        this._handleReservationStatusChange(reservation);
      } catch (error) {
        console.error('[customerReservationMixin] check failed:', error);
        this.reservationCheckError = error;
        this._handleReservationStatusChange(null, error);
      } finally {
        this.reservationCheckLoading = false;
      }
    },

    _handleReservationStatusChange(reservation, error = null) {
      this.reservationStatus = reservation;
      this.disableExchange = this._shouldBlockExchange(reservation);

      if (typeof this.onReservationStatusUpdated === 'function') {
        this.onReservationStatusUpdated(reservation, error);
      }
    },

    _shouldBlockExchange(reservation) {
      if (!reservation) {
        return false;
      }

      return reservation.status === 'pending' || reservation.status === 'rejected';
    },

    _resetReservationState() {
      this.reservationStatus = null;
      this.disableExchange = false;
      this.reservationCheckError = null;

      if (typeof this.onReservationStatusCleared === 'function') {
        this.onReservationStatusCleared();
      }
    },
  },
};
