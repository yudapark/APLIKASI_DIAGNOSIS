document.addEventListener('DOMContentLoaded', () => {
  if (window.lucide) lucide.createIcons();

  // ============ Identifikasi (dependent dropdown) ============
  const brandSelect = document.getElementById('brandSelect');
  const familySelect = document.getElementById('familySelect');
  const modelSelect = document.getElementById('modelSelect');
  const processorSelect = document.getElementById('processorSelect');
  const modelInfo = document.getElementById('modelInfo');
  const modelInfoBody = document.getElementById('modelInfoBody');

  if (brandSelect && familySelect && modelSelect) {
    brandSelect.addEventListener('change', async () => {
      familySelect.innerHTML = '<option value="">— Pilih keluarga —</option>';
      modelSelect.innerHTML = '<option value="">— Pilih model —</option>';
      if (processorSelect) {
        processorSelect.innerHTML = '<option value="">— Pilih prosesor —</option>';
        processorSelect.disabled = true;
      }
      modelSelect.disabled = true;
      if (modelInfo) modelInfo.style.display = 'none';
      if (!brandSelect.value) {
        familySelect.disabled = true;
        return;
      }
      familySelect.disabled = true;
      try {
        const res = await fetch(`/api/families/${brandSelect.value}`);
        const data = await res.json();
        data.forEach(f => {
          const opt = document.createElement('option');
          opt.value = f.id;
          opt.textContent = f.name;
          familySelect.appendChild(opt);
        });
        familySelect.disabled = false;
      } catch (e) {
        console.error(e);
      }
    });

    familySelect.addEventListener('change', async () => {
      modelSelect.innerHTML = '<option value="">— Pilih model —</option>';
      if (processorSelect) {
        processorSelect.innerHTML = '<option value="">— Pilih prosesor —</option>';
        processorSelect.disabled = true;
      }
      if (modelInfo) modelInfo.style.display = 'none';
      if (!familySelect.value) {
        modelSelect.disabled = true;
        return;
      }
      try {
        const res = await fetch(`/api/models/${familySelect.value}`);
        const data = await res.json();
        data.forEach(m => {
          const opt = document.createElement('option');
          opt.value = m.id;
          opt.textContent = m.name + (m.year ? ` (${m.year})` : '');
          modelSelect.appendChild(opt);
        });
        modelSelect.disabled = false;
      } catch (e) {
        console.error(e);
      }
    });

    modelSelect.addEventListener('change', async () => {
      if (processorSelect) {
        processorSelect.innerHTML = '<option value="">— Pilih prosesor —</option>';
        processorSelect.disabled = true;
      }
      if (modelInfo) modelInfo.style.display = 'none';
      if (!modelSelect.value) return;

      try {
        const res = await fetch(`/api/processors/${modelSelect.value}`);
        const procs = await res.json();
        if (processorSelect) {
          procs.forEach(p => {
            const opt = document.createElement('option');
            opt.value = p.processor;
            opt.textContent = p.processor;
            processorSelect.appendChild(opt);
          });
          processorSelect.disabled = procs.length === 0;
        }

        const info = await fetch(`/api/model-detail/${modelSelect.value}`);
        const d = await info.json();
        if (modelInfoBody && modelInfo) {
          const gpuOpts = (d.gpu_options || []).map(g => g.name).join(', ');
          const gpuText = gpuOpts || d.gpu || 'Informasi belum tersedia';
          const coolOpts = (d.cooling_options || []).map(c => {
            const parts = [c.name];
            if (c.fan_count != null) parts.push(c.fan_count + ' fan');
            if (c.heatpipe_count != null) parts.push(c.heatpipe_count + ' heatpipe');
            if (c.has_vapor_chamber) parts.push('vapor chamber');
            return parts.join(' · ');
          }).join('; ');
          const coolText = coolOpts || d.cooling_info || 'Belum tersedia';
          modelInfoBody.innerHTML = `
            <div><span class="label">Merek</span><span class="value">${d.brand_name || '-'}</span></div>
            <div><span class="label">Keluarga</span><span class="value">${d.family_name || '-'}</span></div>
            <div><span class="label">Model</span><span class="value">${d.name || '-'}</span></div>
            <div><span class="label">Generasi</span><span class="value">${d.generation || 'Informasi belum tersedia'}</span></div>
            <div><span class="label">Tahun</span><span class="value">${d.year || '-'}</span></div>
            <div><span class="label">GPU</span><span class="value">${gpuText}</span></div>
            <div><span class="label">Pendinginan</span><span class="value">${coolText}</span></div>
          `;
          modelInfo.style.display = 'block';
          if (window.lucide) lucide.createIcons();
        }
      } catch (e) {
        console.error(e);
      }
    });
  }

  // Toggle form manual
  const toggleManualBtn = document.getElementById('toggleManualBtn');
  const manualFormWrap = document.getElementById('manualFormWrap');
  if (toggleManualBtn && manualFormWrap) {
    toggleManualBtn.addEventListener('click', () => {
      const isHidden = manualFormWrap.style.display === 'none';
      manualFormWrap.style.display = isHidden ? 'block' : 'none';
      if (window.lucide) lucide.createIcons();
    });
  }

  // ============ Admin: family select dependent on brand ============
  const adminBrandSelect = document.getElementById('adminBrandSelect');
  const adminFamilySelect = document.getElementById('adminFamilySelect');
  if (adminBrandSelect && adminFamilySelect) {
    adminBrandSelect.addEventListener('change', async () => {
      adminFamilySelect.innerHTML = '<option value="">— Pilih keluarga —</option>';
      if (!adminBrandSelect.value) return;
      try {
        const res = await fetch(`/api/families/${adminBrandSelect.value}`);
        const data = await res.json();
        data.forEach(f => {
          const opt = document.createElement('option');
          opt.value = f.id;
          opt.textContent = f.name;
          adminFamilySelect.appendChild(opt);
        });
      } catch (e) {
        console.error(e);
      }
    });
  }

  // ============ Form konsultasi ============
  const form = document.getElementById('diagnosisForm');
  const submitBtn = document.getElementById('submitBtn');
  const resetBtn = document.getElementById('resetBtn');
  const counter = document.getElementById('selectionCount');

  if (form) {
    const checkboxes = form.querySelectorAll('input[name="gejala"]');
    const updateCount = () => {
      const n = document.querySelectorAll('input[name="gejala"]:checked').length;
      if (counter) counter.textContent = `${n} dipilih`;
    };
    checkboxes.forEach(cb => cb.addEventListener('change', updateCount));
    updateCount();

    if (resetBtn) {
      resetBtn.addEventListener('click', () => {
        form.querySelectorAll('input[type="checkbox"]').forEach(c => (c.checked = false));
        updateCount();
      });
    }

    if (submitBtn) {
      form.addEventListener('submit', (e) => {
        const n = document.querySelectorAll('input[name="gejala"]:checked').length;
        if (n === 0) {
          e.preventDefault();
          form.animate(
            [
              { transform: 'translateX(0)' },
              { transform: 'translateX(-6px)' },
              { transform: 'translateX(6px)' },
              { transform: 'translateX(0)' },
            ],
            { duration: 260 }
          );
          return;
        }
        submitBtn.classList.add('loading');
      });
    }
  }
});
